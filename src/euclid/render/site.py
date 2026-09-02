"""Building the site: choosing each figure, and writing the files.

The corpus is audited once here and the result shared, because it
used to be measured twice at different strengths and the two numbers
reached different pages.
"""

from __future__ import annotations

import html
import math
import random
from pathlib import Path
from typing import Optional
from ..elements.registry import (
    BadConfiguration,
    ProofFailure,
    Proposition,
    all_propositions,
    run_sampled,
)
from ..plane.construct import GeometryError
from ..plane.trace import Trace
from ..verify.fuzz import certify
from ..verify.ledger import audit
from .svg import _bounds, _collect
from .style import STYLE, _slug
from .pages import (
    _book_x_page,
    _findings_page,
    _graph_page,
    _index_page,
    _ledger_page,
    _minimal_page,
    _optimizer_page,
    _proposition_page,
    _text_page,
)


__all__ = ["build"]


def _legibility(trace: Trace) -> float:
    """How well a sampled figure reads, from 0 (unreadable) to 1.

    Presentation only, and deliberately kept away from anything that is
    checked: verification samples widely on purpose, and a near-degenerate
    triangle is a *better* test than a comfortable one. It is only a worse
    picture. So the wide sampling stays, and the one configuration put on the
    page is chosen from among many for being the one a reader can see.

    Two things decide it. A figure squeezed into a sliver wastes the frame, so
    the shape of the bounding box counts; and labels that collide are unreadable
    whatever the shape, so the closest pair of points counts too.
    """
    points, _, _ = _collect(trace)
    if len(points) < 2:
        return 0.0
    left, bottom, right, top = _bounds(points, [])
    width, height = right - left, top - bottom
    diagonal = math.hypot(width, height)
    if diagonal <= 0:
        return 0.0
    shape = min(width, height) / max(width, height)

    placed = [point.as_floats() for point in points]
    closest = min(
        math.dist(placed[i], placed[j])
        for i in range(len(placed))
        for j in range(i + 1, len(placed))
    )
    # A gap of a twentieth of the diagonal is enough to letter two points apart.
    separation = min(1.0, (closest / diagonal) / 0.05)
    return shape * separation


def _sample_trace(entry: Proposition, seed: int = 3, tries: int = 120) -> Optional[Trace]:
    """The clearest figure among many valid ones.

    Forty tries was enough while figures were small.  Carrying out citations made
    the densest ones denser -- I.44 draws thirty-eight points now, where it drew
    twenty-nine -- and forty configurations of those no longer contained a legible
    one: I.44 scored 0.30 and I.45 0.21, both under the threshold this is for.
    At a hundred and twenty they score 0.59 and 0.63, and at three hundred they
    score the same, so the readable configurations were there and the search was
    stopping short of them. The early exit below means only a figure that never
    reaches 0.75 pays for the higher cap.
    """
    if entry.sample is None:
        return None
    from ..elements import samples

    rng = random.Random(f"site:{entry.ref}:{seed}")
    best: Optional[Trace] = None
    best_score = -1.0
    with samples.comfortable():
        for _ in range(tries):
          try:
              trace = run_sampled(entry.ref, rng).trace
          except (BadConfiguration, GeometryError, ProofFailure):
              continue
          # Books V and VII to X argue about magnitudes and draw nothing, so
          # there is no figure to choose between: searching forty configurations
          # for the clearest of them is forty runs spent on a picture that does
          # not exist. Two hundred and forty of the three hundred and ninety
          # propositions are in that case.
          if not _collect(trace)[1] and not _collect(trace)[2]:
              return trace
          score = _legibility(trace)
          if score > best_score:
              best, best_score = trace, score
          if best_score > 0.75:  # good enough; stop paying for the search
              break
    return best


def build(destination: Path, run_search: bool = True) -> list[Path]:
    """Generate the whole site.  Returns the files written."""
    from ..graph import build as build_graph
    from ..search import PROBLEMS, solve

    destination.mkdir(parents=True, exist_ok=True)
    graph = build_graph()
    written: list[Path] = []

    (destination / "style.css").write_text(STYLE, encoding="utf-8")
    written.append(destination / "style.css")

    def write(name: str, text: str) -> None:
        path = destination / name
        path.write_text(text, encoding="utf-8")
        written.append(path)

    # The ledger is audited once and shared. It used to be computed twice at
    # different trial counts -- trials=3 here and trials=8 on the ledger page --
    # so the index and the findings page reported 355 unproved assumptions while
    # the ledger page reported 350, from the same build. One number, one source.
    claims = 0
    ledgers = []
    for entry in all_propositions():
        trace = _sample_trace(entry)
        claims += certify(entry.ref, trials=4).claims_checked
        ledger = audit(entry.ref, trials=8)
        ledgers.append(ledger)
        write(f"{_slug(entry.ref)}.html",
              _proposition_page(entry, graph, trace, ledger))

    stats = {
        "claims": claims,
        "continuity": sum(item.continuity_debt for item in ledgers),
        "order": sum(len(item.of_kind("order")) for item in ledgers),
        "varies": [item.ref for item in ledgers if item.of_kind("case")],
        "edges": sum(len(e) for e in graph.edges.values()),
    }

    # The construction searches come from findings.json, not from this build.
    # Running them here meant only the shallow ones ever ran -- max_depth=5 on
    # the default instruction set -- while the pages stated a compass-only
    # result that no build and no test computed. Recording them is what lets a
    # four-minute search stand behind a sentence. `run_search` now only decides
    # whether to show them, not whether they exist.
    from ..measure import load_findings

    measured = load_findings() or {}
    search_rows = []
    if run_search:
        for row in measured.get("constructions", []):
            steps = None
            reference = row.get("euclid")
            if reference and reference in graph.nodes:
                trace = _sample_trace(graph.nodes[reference])
                steps = trace.step_count if trace else None
            search_rows.append((reference, steps, row))

    write("index.html", _index_page(graph, stats))
    write("findings.html", _findings_page(graph, stats, search_rows))
    write("graph.html", _graph_page(graph))
    write("minimal.html", _minimal_page(graph))
    write("ledger.html", _ledger_page(ledgers))
    write("optimizer.html", _optimizer_page(search_rows))
    write("book-x.html", _book_x_page())
    write("text.html", _text_page())
    return written
