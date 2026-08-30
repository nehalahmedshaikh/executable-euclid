"""Diagrams, drawn from execution traces.

No figure in this project is drawn by hand or positioned by eye.  Each one is
the record of a construction that ran and verified, so what you see is exactly
what the machine checked.

These are different in kind from
the figures printed with Euclid.  His are *composed*: he picks a configuration
that shows the case well, draws only the arcs the argument needs, and letters
the points to suit.  These are *traces*: the coordinates come from a sampler,
the objects are whatever the code made, and the lettering follows the
parameters.  They will not resemble his, and tuning them until they do would
mean drawing something other than what ran.

What the renderer can do is give the trace a hierarchy, so the subject is not
lost in the apparatus.  A proposition's own lines and points are drawn firm;
the ones it inherited from helper constructions are drawn back, in thin grey,
unlettered.  Nothing is hidden -- every object the construction made is still on
the page.  Where the answer itself was built by a helper, the proposition says
so with ``plane.construct.result`` and that marking wins instead.
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


def _spanning(segments: list[Line]) -> Line:
    """One segment covering every segment drawn on the same straight line.

    Two segments of one line are *equal* as lines -- that is what makes ``Line``
    equality structural -- so collecting them naively keeps only whichever came
    first. When that one was the shorter, the rest of the line vanished from the
    figure: a line cut at a point would be drawn as far as the cut and no
    further, leaving the far end a dot with nothing joining it to anything.
    Taking the outermost endpoints draws all of what was drawn.
    """
    first = segments[0]
    origin = first.p
    dx, dy = first.q.x - origin.x, first.q.y - origin.y
    near = far = origin
    lowest = highest = None
    for segment in segments:
        for point in (segment.p, segment.q):
            reach = (point.x - origin.x) * dx + (point.y - origin.y) * dy
            if lowest is None or reach < lowest:
                lowest, near = reach, point
            if highest is None or reach > highest:
                highest, far = reach, point
    if near == far:
        return first
    return Line.through(near, far, first.label)


def _the_propositions_own(trace: Trace) -> tuple[set, dict]:
    """What this proposition drew and lettered itself, as against its helpers'.

    A figure-level move fans out to every enclosing trace, because a caller's
    diagram really does contain its callee's lines. The consequence is that a
    proposition standing on two or three helpers inherits nearly all of what is
    drawn: I.3 draws only eight of the twenty-six objects in its own figure, and
    I.10 four of thirty-three. Rendered at one weight, the subject is lost in
    the apparatus that found it.

    Ownership is decided by the *move*, not the object. A move is inherited if
    it is also in some descendant trace -- the same ``Move`` instance is in both
    lists -- and a point given to a proposition and passed down to a helper is
    therefore still the proposition's own, because its own registration of it
    was its own move.

    That also settles the lettering. Helpers name their parameters from
    scratch, so one spot on the page is A to a caller and D to its callee; the
    caller's own naming is the one to show.
    """
    inherited = {id(move) for child in trace.descendants() for move in child.moves}
    own: set = set()
    labels: dict = {}
    for move in trace.moves:
        if move.obj is None or id(move) in inherited:
            continue
        own.add(move.obj)
        if isinstance(move.obj, Point) and move.label:
            labels.setdefault(move.obj, move.label)
    return own, labels


def _collect(trace: Trace) -> tuple[list[Point], list[Line], list[Circle]]:
    points: list[Point] = []
    order: list[Line] = []
    on_the_same_line: dict[Line, list[Line]] = {}
    circles: list[Circle] = []
    for move in trace.moves:
        item = move.obj
        if isinstance(item, Point):
            if item not in points:
                points.append(item)
        elif isinstance(item, Line):
            if item not in on_the_same_line:
                on_the_same_line[item] = []
                order.append(item)
            on_the_same_line[item].append(item)
        elif isinstance(item, Circle):
            if item not in circles:
                circles.append(item)
    lines = [_spanning(on_the_same_line[key]) for key in order]
    return points, lines, circles


def _bounds(points, circles) -> tuple[float, float, float, float]:
    """Frame the figure on its points, and let the arcs run off the edge.

    A circle drawn to *find* a point is usually far larger than the figure it
    was drawn for: I.1's two circles are twice the triangle in every direction,
    so fitting them in left the triangle across a seventh of the picture, and
    twenty of the figures here were dwarfed the same way. Euclid has the same
    circles and the same problem, and solves it by drawing only the arc he
    needs. Framing on the points and clipping is the same economy reached from
    the other side: the arcs still sweep through, but the figure is the subject.

    A circle that *is* the subject -- Book III's, Book IV's -- costs nothing,
    because its points lie on it and the frame takes them in anyway.
    """
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        x, y = point.as_floats()
        xs.append(x)
        ys.append(y)
    if not xs:
        for circle in circles:
            cx, cy = circle.centre.as_floats()
            radius = circle.radius_float()
            xs += [cx - radius, cx + radius]
            ys += [cy - radius, cy + radius]
    if not xs:
        return -1.0, -1.0, 1.0, 1.0
    left, bottom, right, top = min(xs), min(ys), max(xs), max(ys)
    # A figure whose points are collinear has no extent across the line, so give
    # it some rather than dividing by nothing.
    if right - left < 1e-9:
        left, right = left - 1.0, right + 1.0
    if top - bottom < 1e-9:
        bottom, top = bottom - 1.0, top + 1.0
    return left, bottom, right, top


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

    The nudge is a fraction of the segment, not of the whole figure. Taken from
    the figure it swamped short segments -- a join a twentieth the width of the
    diagram grew stubs as long as itself, which read as marks in their own right.
    """
    first, second = line.p.as_floats(), line.q.as_floats()
    span = math.dist(first, second)
    if span < 1e-12:
        return None
    nudge = min(0.04 * reach, 0.12 * span) / span
    dx, dy = second[0] - first[0], second[1] - first[1]
    start = (first[0] - dx * nudge, first[1] - dy * nudge)
    end = (second[0] + dx * nudge, second[1] + dy * nudge)
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
    own, own_labels = _the_propositions_own(trace)
    # What the proposition did itself is the figure; what its helpers did is
    # scaffolding, and is drawn back. A proposition that names a result says so
    # explicitly, which is the only way to feature something a helper built --
    # I.44's answer is a parallelogram I.42 made.
    answer = set(trace.results)
    featured = (lambda item: item in answer) if answer else (lambda item: item in own)
    marked_labels = {
        item: item.label for item in trace.results if isinstance(item, Point) and item.label
    }

    reach = max(right - left, top - bottom, 1e-9)
    # Held-back objects go down first, so the answer is drawn over them.
    for held_back in (True, False):
        suffix = " aside" if held_back else ""
        group: list[str] = []
        for circle in circles:
            if featured(circle) is held_back:
                continue
            cx, cy = circle.centre.as_floats()
            centre = frame.place(cx, cy)
            radius = circle.radius_float() * frame.scale
            group.append(
                f'<circle cx="{centre[0]:.2f}" cy="{centre[1]:.2f}" r="{radius:.2f}" '
                f'fill="none" class="arc{suffix}"/>'
            )
        for line in lines:
            if featured(line) is held_back:
                continue
            segment = _draw_line(line, frame, reach)
            if segment:
                group.append(
                    f'<line x1="{segment[0]:.2f}" y1="{segment[1]:.2f}" '
                    f'x2="{segment[2]:.2f}" y2="{segment[3]:.2f}" class="ray{suffix}"/>'
                )
        if group:
            parts.append(f'<g class="construction{suffix}">')
            parts.extend(group)
            parts.append("</g>")

    parts.append('<g class="points">')
    # One letter, one point: a helper's naming of a spot the proposition has
    # already named itself is dropped rather than printed twice.
    spoken_for: set[str] = set()
    for point in points:
        x, y = frame.place(*point.as_floats())
        if not featured(point):
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.5" class="dot aside"/>')
            continue
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" class="dot"/>')
        letter = marked_labels.get(point) or own_labels.get(point) or point.label
        if letter and letter not in spoken_for:
            spoken_for.add(letter)
            parts.append(
                f'<text x="{x + 7:.2f}" y="{y - 7:.2f}" class="letter">{letter}</text>'
            )
    parts.append("</g></svg>")
    return "".join(parts)


def svg_document(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}'
