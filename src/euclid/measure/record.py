"""The measurements, computed once and written down.

Running the whole corpus to answer one question takes minutes -- the depth
profile executes all 390 propositions, and the necessity analysis executes each
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

import json
from pathlib import Path
from typing import Optional

from ..elements.registry import all_propositions
from .depth import ceilings, depth_profile, first_appearances
from .gaps import named_count, taxonomy_gaps
from .necessity import necessity_report

__all__ = ["FINDINGS_PATH", "load_findings", "write_findings"]

FINDINGS_PATH = Path(__file__).with_name("findings.json")


def write_findings(trials: int = 48, path: Optional[Path] = None) -> dict:
    """Compute every measurement and write it down.

    The necessity trials are worth paying for: each proposition has a plan of
    perturbations roughly quadratic in its number of points, and a trial spends
    one of them, so coverage climbs with the count -- 36% at sixteen, 45% at
    forty-eight.
    """
    path = path or FINDINGS_PATH
    profile = depth_profile()
    report = necessity_report(trials=trials)
    gaps = taxonomy_gaps(limit=6)
    named, unnamed = named_count()

    payload = {
        "corpus": len(all_propositions()),
        "method": (
            "Every number here was computed by running the corpus. Depth is exact. "
            "The necessity figures are empirical: a hypothesis is broken by moving "
            "one given, and what survives is a candidate, not a theorem."
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
            "propositions": report.propositions_tried,
            "hypotheses": report.hypotheses_total,
            "judged": len(report.tested),
            "coverage": round(report.coverage, 4),
            "needed": sum(1 for i in report.tested if i.verdict == "needed"),
            "well_defined": sum(1 for i in report.tested if i.verdict == "well-definedness"),
            "candidates": [
                {"ref": i.ref, "text": i.text, "configurations": i.broken}
                for i in sorted(report.candidates, key=lambda x: -x.broken)
            ],
        },
        "constructions": _constructions(),
        "fields": _fields(),
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
            for ref in ("I.1", "I.20")
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
