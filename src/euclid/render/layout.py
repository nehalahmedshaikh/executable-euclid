"""Layered layout for the dependency graph, drawn as inline SVG.

Propositions are placed on rows by their depth in the graph, so the postulates
sit at the bottom and the results that lean on everything float to the top.
Within a row they keep Euclid's own ordering, which makes the picture readable
as a map of the book rather than a hairball.
"""

from __future__ import annotations

from typing import Iterable, Optional

__all__ = ["graph_svg"]

COLUMN = 78
ROW = 74
MARGIN = 44

# A row of 129 propositions is 10,000px wide. Scaled to fit a page it becomes a
# grey smear -- an 11px label rendered at one pixel. So the SVG carries its
# natural width and height and the page scrolls it instead of shrinking it.
# Where a graph is short enough to fit, nothing scrolls and nothing is lost.
TIGHT_ROW = 52  # a near-linear chain wastes less height than a broad one


def graph_svg(
    graph,
    refs: Optional[Iterable[str]] = None,
    highlight: Optional[str] = None,
    only_executed: bool = False,
) -> str:
    """Lay the chosen propositions out by depth and draw them at natural size.

    With ``only_executed`` the picture is restricted to edges recorded as calls,
    dropping the citations.  That is a much smaller graph -- and the only one
    that is an observation rather than a transcription.
    """
    chosen = [ref for ref in (list(refs) if refs is not None else list(graph.nodes))]
    if not chosen:
        return ""
    selected = set(chosen)

    rows: dict[int, list[str]] = {}
    for ref in chosen:
        rows.setdefault(graph.depth(ref), []).append(ref)
    for level in rows:
        rows[level].sort(key=lambda ref: graph.nodes[ref].sort_key())

    widest = max(len(members) for members in rows.values())
    # A tall thin ladder (the tree-shaken sets are mostly one node per row) is
    # all dead space at full row height.
    row_height = ROW if widest > 3 else TIGHT_ROW
    width = MARGIN * 2 + max(widest, 1) * COLUMN
    height = MARGIN * 2 + (max(rows) + 1) * row_height

    position: dict[str, tuple[float, float]] = {}
    for level, members in rows.items():
        indent = (width - len(members) * COLUMN) / 2 + COLUMN / 2
        for index, ref in enumerate(members):
            position[ref] = (indent + index * COLUMN, height - MARGIN - level * row_height)

    parts = [
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" '
        f'height="{height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        'class="graph" role="img" aria-label="dependency graph">'
    ]
    parts.append('<g class="edges">')
    for ref in chosen:
        x2, y2 = position[ref]
        wanted = graph.executed.get(ref, set()) if only_executed else graph.needs(ref)
        for required in sorted(wanted & selected):
            x1, y1 = position[required]
            midpoint = (y1 + y2) / 2
            emphasis = " lit" if highlight and ref == highlight else ""
            # Solid where the call was recorded as it happened; dashed where the
            # reference was written beside the step by hand. Most are dashed, and
            # the picture says so.
            if required in graph.executed.get(ref, ()):
                kind = ""
            else:
                kind = " cited"
            parts.append(
                f'<path d="M {x1:.1f} {y1:.1f} C {x1:.1f} {midpoint:.1f}, '
                f'{x2:.1f} {midpoint:.1f}, {x2:.1f} {y2:.1f}" '
                f'class="edge{kind}{emphasis}"/>'
            )
    parts.append("</g><g class=\"nodes\">")
    for ref in chosen:
        x, y = position[ref]
        classes = "node" + (" lit" if ref == highlight else "")
        parts.append(
            f'<a href="{ref.replace(".", "-")}.html">'
            f'<rect x="{x - 27:.1f}" y="{y - 13:.1f}" width="54" height="26" rx="5" '
            f'class="{classes}"/>'
            f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" class="node-label">'
            f"{ref}</text></a>"
        )
    parts.append("</g></svg>")
    return "".join(parts)
