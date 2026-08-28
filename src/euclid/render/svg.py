"""Diagrams, drawn from execution traces.

No figure in this project is drawn by hand or positioned by eye.  Each one is
the record of a construction that ran and verified, so what you see is exactly
what the machine checked -- construction arcs faint, results firm, points
lettered as the proposition lettered them.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional

from ..kernel.field import to_float
from ..plane.objects import Circle, Line, Point
from ..plane.trace import Trace

__all__ = ["render_trace", "svg_document"]

WIDTH = 520
HEIGHT = 380
PADDING = 34


def _collect(trace: Trace) -> tuple[list[Point], list[Line], list[Circle]]:
    points: list[Point] = []
    lines: list[Line] = []
    circles: list[Circle] = []
    for move in trace.moves:
        item = move.obj
        if isinstance(item, Point):
            if item not in points:
                points.append(item)
        elif isinstance(item, Line):
            if item not in lines:
                lines.append(item)
        elif isinstance(item, Circle):
            if item not in circles:
                circles.append(item)
    return points, lines, circles


def _bounds(points, circles) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        x, y = point.as_floats()
        xs.append(x)
        ys.append(y)
    for circle in circles:
        cx, cy = circle.centre.as_floats()
        radius = circle.radius_float()
        xs += [cx - radius, cx + radius]
        ys += [cy - radius, cy + radius]
    if not xs:
        return -1.0, -1.0, 1.0, 1.0
    return min(xs), min(ys), max(xs), max(ys)


class _Frame:
    """Maps model coordinates onto the picture, y flipped so north is up."""

    def __init__(self, left: float, bottom: float, right: float, top: float) -> None:
        span_x = max(right - left, 1e-9)
        span_y = max(top - bottom, 1e-9)
        self.scale = min((WIDTH - 2 * PADDING) / span_x, (HEIGHT - 2 * PADDING) / span_y)
        self.left, self.bottom = left, bottom
        self.offset_x = (WIDTH - span_x * self.scale) / 2
        self.offset_y = (HEIGHT - span_y * self.scale) / 2
        self.span_y = span_y

    def place(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.offset_x + (x - self.left) * self.scale,
            HEIGHT - self.offset_y - (y - self.bottom) * self.scale,
        )


def _draw_line(line: Line, frame: _Frame, reach: float) -> Optional[tuple]:
    """Draw the segment between the two points that defined the line.

    Euclid's figures are made of segments, not infinite lines: he joins A to B,
    and produces a line only as far as he needs it, naming the far end. So the
    faithful rendering of ``line(A, B)`` is the segment AB, nudged out slightly
    at each end to show it is a line and not merely a join.
    """
    first, second = line.p.as_floats(), line.q.as_floats()
    span = math.dist(first, second)
    if span < 1e-12:
        return None
    overhang = 0.05 * reach / span
    dx, dy = second[0] - first[0], second[1] - first[1]
    start = (first[0] - dx * overhang, first[1] - dy * overhang)
    end = (second[0] + dx * overhang, second[1] + dy * overhang)
    return frame.place(*start) + frame.place(*end)


def render_trace(trace: Trace, title: str = "") -> str:
    """One proposition's figure, as a self-contained SVG fragment."""
    points, lines, circles = _collect(trace)
    if not points and not circles:
        return ""
    left, bottom, right, top = _bounds(points, circles)
    frame = _Frame(left, bottom, right, top)

    parts = [
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{title or trace.proposition}" class="figure">'
    ]
    parts.append('<g class="construction">')
    for circle in circles:
        cx, cy = circle.centre.as_floats()
        centre = frame.place(cx, cy)
        radius = circle.radius_float() * frame.scale
        parts.append(
            f'<circle cx="{centre[0]:.2f}" cy="{centre[1]:.2f}" r="{radius:.2f}" '
            f'fill="none" class="arc"/>'
        )
    reach = max(right - left, top - bottom, 1e-9)
    for line in lines:
        segment = _draw_line(line, frame, reach)
        if segment:
            parts.append(
                f'<line x1="{segment[0]:.2f}" y1="{segment[1]:.2f}" '
                f'x2="{segment[2]:.2f}" y2="{segment[3]:.2f}" class="ray"/>'
            )
    parts.append("</g>")

    parts.append('<g class="points">')
    for point in points:
        x, y = frame.place(*point.as_floats())
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" class="dot"/>')
        if point.label:
            parts.append(
                f'<text x="{x + 7:.2f}" y="{y - 7:.2f}" class="letter">{point.label}</text>'
            )
    parts.append("</g></svg>")
    return "".join(parts)


def svg_document(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}'
