"""The measurements, computed once and written down.

Running the whole corpus to answer one question takes minutes -- the depth
profile executes the full corpus, and the necessity analysis executes each
of them once per configuration it perturbs. Doing that inside a site build would
make the build unusable and CI worse.

So the numbers are computed on demand, written to ``findings.json`` beside this
module, and committed. The site reads the file; nothing on a page is computed at
render time. That has the same shape as ``heath.json``: a artefact you can read,
diff and argue with.

Regenerate with ``euclid measure --write``. The file records the corpus size it
was computed from, so a stale one can be spotted.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import pickle
from pathlib import Path
from typing import Callable, Optional

from ..elements.registry import all_propositions
from .depth import ceilings, depth_profile, first_appearances
from .gaps import named_count, taxonomy_gaps
from .mutation import mutation_report
from .necessity import necessity_report

__all__ = ["FINDINGS_PATH", "RECORDED_TRIALS", "load_findings", "write_findings"]

FINDINGS_PATH = Path(__file__).with_name("findings.json")

# The strength the recorded file is computed at, in one place because it was in
# two. ``write_findings`` defaulted to forty-eight and the ``--trials`` flag of
# ``euclid measure`` defaulted to sixteen, so the command this module names as
# the way to regenerate produced a materially weaker file than the one beside
# it: coverage 36% against 45%, and nine candidates the stronger run does not
# report. The count is written into the payload so a file computed at some
# other strength can be told apart from this one.
RECORDED_TRIALS = 48


def _source_fingerprint() -> str:
    root = Path(__file__).resolve().parents[3]
    digest = hashlib.sha256()
    for source in sorted((root / "src" / "euclid").rglob("*.py")):
        digest.update(str(source.relative_to(root)).encode())
        digest.update(source.read_bytes())
    return digest.hexdigest()


def _save_checkpoint(path: Path, trials: int, fingerprint: str, results: dict) -> None:
    """Atomically preserve completed stages so Ctrl-C can be resumed safely."""
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(pickle.dumps({"trials": trials, "fingerprint": fingerprint, "results": results}))
    temporary.replace(path)


def write_findings(
    trials: int = RECORDED_TRIALS,
    path: Optional[Path] = None,
    jobs: int = 1,
    progress: Optional[Callable[[str], None]] = None,
    resume: bool = False,
) -> dict:
    """Compute every measurement and write it down.

    The necessity trials are worth paying for: each proposition has a plan of
    perturbations roughly quadratic in its number of points, and a trial spends
    one of them, so coverage climbs with the count -- 36% at sixteen, 45% at
    forty-eight.

    The expensive stages are independent and deterministic, so ``jobs``
    executes them in separate processes. The single-job path is retained for
    callers that need to avoid child processes.
    """
    if jobs < 1:
        raise ValueError("jobs must be at least one")
    path = path or FINDINGS_PATH
    checkpoint = Path(".euclid-cache") / f"findings-{trials}.pickle"
    fingerprint = _source_fingerprint()
    results = {}
    if resume and checkpoint.exists():
        saved = pickle.loads(checkpoint.read_bytes())
        if saved.get("trials") == trials and saved.get("fingerprint") == fingerprint:
            results = saved.get("results", {})
            if progress is not None:
                for name in results:
                    progress(f"cached {name}")
    stages = [
        ("algebraic depth", depth_profile, ()),
        ("hypothesis necessity", necessity_report, (None, trials)),
        ("claim mutation", mutation_report, (None, trials)),
        ("construction searches", _constructions, ()),
        ("field ladder", _fields, ()),
    ]
    checkpoint.parent.mkdir(exist_ok=True)
    remaining = [stage for stage in stages if stage[0] not in results]
    if jobs == 1:
        for name, function, arguments in remaining:
            results[name] = function(*arguments)
            _save_checkpoint(checkpoint, trials, fingerprint, results)
            if progress is not None:
                progress(name)
    else:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            pending = {
                pool.submit(function, *arguments): name
                for name, function, arguments in remaining
            }
            for future in as_completed(pending):
                name = pending[future]
                results[name] = future.result()
                _save_checkpoint(checkpoint, trials, fingerprint, results)
                if progress is not None:
                    progress(name)

    profile = results["algebraic depth"]
    report = results["hypothesis necessity"]
    claims = results["claim mutation"]
    gaps = taxonomy_gaps(limit=6)
    named, unnamed = named_count()

    payload = {
        "corpus": len(all_propositions()),
        "method": (
            "Every number here was computed by running the corpus. Depth is exact. "
            "The necessity and mutation figures are empirical: one given is bent, and "
            "what survives the bending is a candidate, not a theorem."
        ),
        "depth": {
            "ceilings": ceilings(profile),
            "first_appearances": {str(k): v for k, v in first_appearances(profile).items()},
            "histogram": _histogram(profile),
            "deepest": [
                {"ref": item.ref, "degree": item.degree, "where": item.where}
                for item in sorted(profile.values(), key=lambda d: -d.degree)[:5]
            ],
        },
        "necessity": {
            "trials": trials,
            "propositions": report.propositions_tried,
            "hypotheses": report.hypotheses_total,
            "judged": len(report.tested) + len(report.implied),
            "separated": len(report.tested),
            "coverage": round(report.coverage, 4),
            "separated_share": round(report.separated, 4),
            "implied": len(report.implied),
            "needed": sum(1 for i in report.tested if i.verdict == "needed"),
            "well_defined": sum(1 for i in report.tested if i.verdict == "well-definedness"),
            "surviving_guards": len(report.surviving_guards),
            "truncated": sorted(report.truncated),
            "candidates": [
                {"ref": i.ref, "text": i.text, "configurations": i.broken}
                for i in sorted(report.candidates, key=lambda x: -x.broken)
            ],
        },
        "mutation": {
            "trials": trials,
            "propositions": claims.propositions_tried,
            "claims": claims.claims_total,
            "live": len(claims.live),
            "coverage": round(claims.coverage, 4),
            "unreached": len(claims.unreached),
            "unfalsified": [
                {"ref": i.ref, "text": i.text, "by": list(i.by), "bends": i.reached}
                for i in sorted(claims.unfalsified, key=lambda x: (x.ref, x.text))
            ],
        },
        "constructions": results["construction searches"],
        "fields": results["field ladder"],
        "book_x_gaps": {
            "candidates_named": named,
            "candidates_unnamed": unnamed,
            "witnesses": [
                {
                    "expression": g.expression,
                    "value": round(g.value_float, 10),
                    "degree": g.degree,
                    "minimal_polynomial": g.minimal_polynomial,
                    "reason": g.reason,
                }
                for g in gaps
            ],
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _fields() -> dict:
    """The field ladder: what each rung of the restriction buys."""
    from .fields import partition

    found = partition(trials=8)
    buckets = found["buckets"]
    return {
        "buckets": {name: sorted(refs) for name, refs in buckets.items()},
        "counts": {name: len(refs) for name, refs in buckets.items()},
        "witnesses": [
            {"ref": ref, "cause": found["rational"][ref].cause,
             "site": found["rational"][ref].site,
             "radicand": found["rational"][ref].radicand}
            # I.1 needs a circle to meet a circle; I.34 only ever measures, so
            # the Pythagorean rung carries it. I.20 used to be the second
            # witness, and stopped being one when citations began to be carried
            # out: it appeals to I.3, I.3 cuts a length with a circle, and the
            # triangle inequality inherited the continuity debt of the step that
            # lays the length off.
            for ref in ("I.1", "I.34")
            if ref in found["rational"] and found["rational"][ref].cause
        ],
    }


def _constructions() -> list[dict]:
    """The shortest-construction searches, run once and written down.

    These used to be computed during the site build, which meant only the
    shallow ones ever ran: the build called ``solve`` at ``max_depth=5`` on the
    default instruction set, so no compass-only result was produced anywhere.
    The site nonetheless stated that the compass alone needs seven circles for a
    midpoint -- a claim no build and no test computed, and which took four
    minutes to confirm when finally run.

    Recording them here is what lets a four-minute search back a sentence on a
    page. Regenerate with ``euclid measure --write``.
    """
    from ..search import PROBLEMS
    from ..search.problems import solve

    wanted = [(name, "full", 5) for name in PROBLEMS]
    # The deep ones. Only compass-only reaches a goal the straightedge cannot,
    # and the midpoint at depth 7 is the Mohr-Mascheroni price.
    wanted += [("equilateral-triangle", "compass-only", 3),
               ("double-a-segment", "compass-only", 4),
               ("midpoint", "compass-only", 7)]

    rows: list[dict] = []
    for name, isa, depth in wanted:
        # Certifying a length means enumerating everything shorter, and for the
        # compass-only midpoint that is depth 6 -- tens of thousands of figures
        # in exact arithmetic. It is worth the minutes: at the default budget
        # the enumeration gives up, and the answer stays the one the float
        # search found, which is wrong.
        budget = 2_000_000 if depth >= 6 else 60_000
        result = solve(name, isa=isa, max_depth=depth, exact_budget=budget)
        rows.append({
            "problem": name,
            "isa": isa,
            "euclid": PROBLEMS[name].euclid,
            "found": result.found,
            "length": result.length if result.found else None,
            "depth_searched": result.depth_searched,
            "verified": result.verified,
            # the two halves of "shortest", which are not equally strong
            "exhaustive": result.exhaustive,        # float search, budget not hit
            "exact_minimal": result.exact_minimal,  # every shorter figure ruled out exactly
            "exact_figures": result.exact_figures,
            "beat_float": result.beat_float,
            "notation": result.geometrography.notation() if result.found else "",
        })
    return rows


def _histogram(profile: dict) -> dict:
    counts: dict[str, int] = {}
    for item in profile.values():
        counts[str(item.degree)] = counts.get(str(item.degree), 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: int(kv[0])))


def load_findings() -> Optional[dict]:
    """What was measured, or None if it has never been computed."""
    if not FINDINGS_PATH.exists():
        return None
    return json.loads(FINDINGS_PATH.read_text(encoding="utf-8"))
