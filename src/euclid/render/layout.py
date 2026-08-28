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


def graph_svg(graph, refs: Optional[Iterable[str]] = None, highlight: Optional[str] = None) -> str:
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
    width = MARGIN * 2 + max(widest, 1) * COLUMN
    height = MARGIN * 2 + (max(rows) + 1) * ROW

    position: dict[str, tuple[float, float]] = {}
    for level, members in rows.items():
        indent = (width - len(members) * COLUMN) / 2 + COLUMN / 2
        for index, ref in enumerate(members):
            position[ref] = (indent + index * COLUMN, height - MARGIN - level * ROW)

    parts = [
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        'class="graph" role="img" aria-label="dependency graph">'
    ]
    parts.append('<g class="edges">')
    for ref in chosen:
        x2, y2 = position[ref]
        for required in sorted(graph.needs(ref) & selected):
            x1, y1 = position[required]
            midpoint = (y1 + y2) / 2
            emphasis = " lit" if highlight and ref == highlight else ""
            parts.append(
                f'<path d="M {x1:.1f} {y1:.1f} C {x1:.1f} {midpoint:.1f}, '
                f'{x2:.1f} {midpoint:.1f}, {x2:.1f} {y2:.1f}" class="edge{emphasis}"/>'
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
