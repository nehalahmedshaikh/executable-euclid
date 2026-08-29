"""The measurements, computed once and written down.

Running the whole corpus to answer one question takes minutes -- the depth
profile executes all 390 propositions, and the necessity analysis executes each
of them once per configuration it perturbs. Doing that inside a site build would
make the build unusable and CI worse.

So the numbers are computed on demand, written to ``findings.json`` beside this
module, and committed. The site reads the file; nothing on a page is computed at
render time. That has the same shape as ``heath.json``: a artefact you can read,
diff and argue with, rather than a number that appears when the page is built.

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


def write_findings(trials: int = 16, path: Optional[Path] = None) -> dict:
    """Compute every measurement and write it down."""
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
