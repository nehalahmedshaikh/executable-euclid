"""Exact arithmetic over the constructible numbers.

A *constructible number* is one reachable from the rationals by field
operations and square roots -- exactly the numbers a straightedge and compass
can produce.  We model them as a **monotonic tower of quadratic extensions**

    Q  subset  Q(sqrt r1)  subset  Q(sqrt r1, sqrt r2)  subset  ...

where each radicand ``r_k`` is guaranteed **not** to be a square in the field
below it.  That guarantee is what makes the representation
``a + b*sqrt(r_k)`` unique, which in turn makes equality *structural* and the
zero test *exact*.  No epsilons appear anywhere in this library.

Two consequences the rest of the project leans on:

* A normalised :class:`Surd` is **never zero**.  If ``a + b*sqrt(r) == 0`` with
  ``b != 0`` then ``sqrt(r) = -a/b`` would live in the base field, contradicting
  the non-square invariant.  So ``is_zero`` is a type check, and ``==`` is a
  structural comparison -- both exact, both O(size of the expression).
* Deciding the *sign* of a nonzero element needs numerics, but only as a
  refinement loop (:func:`sign`).  Because the zero test is decisive, the loop
  always terminates.

Maintaining the non-square invariant is the job of :func:`sqrt`, which first
tries to *find* the root inside the existing tower and only extends when it
genuinely cannot.  See :func:`_exact_sqrt`.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Optional, Union

from .numeric import Interval

__all__ = [
    "Constructible",
    "Context",
    "Surd",
    "Tower",
    "current_tower",
    "is_zero",
    "sign",
    "sqrt",
    "to_float",
]

ZERO = Fraction(0)
ONE = Fraction(1)
HALF = Fraction(1, 2)

Constructible = Union[Fraction, "Surd"]

MAX_SIGN_PRECISION = 1 << 18


class Tower:
    """The chain of quadratic extensions built up during one construction."""

    __slots__ = ("radicands", "_sqrt_memo", "_interval_memo")

    def __init__(self) -> None:
        self.radicands: list[Constructible] = []
        self._sqrt_memo: dict = {}
        self._interval_memo: dict = {}

    @property
    def depth(self) -> int:
        return len(self.radicands)

    def radicand(self, level: int) -> Constructible:
        return self.radicands[level - 1]

    def extend(self, r: Constructible) -> "Surd":
        """Adjoin ``sqrt(r)``.  The caller must have shown ``r`` is a non-square."""
        self.radicands.append(r)
        return Surd(self, self.depth, ZERO, ONE)

    def describe(self) -> str:
        if not self.radicands:
            return "Q"
        return "Q(" + ", ".join(f"sqrt({fmt(r)})" for r in self.radicands) + ")"


class Surd:
    """``a + b*sqrt(r_level)`` with ``b`` nonzero and ``a``, ``b`` below ``level``."""

    __slots__ = ("tower", "level", "a", "b", "_hash")

    def __init__(self, tower: Tower, level: int, a: Constructible, b: Constructible) -> None:
        self.tower = tower
        self.level = level
        self.a = a
        self.b = b
        self._hash: Optional[int] = None

    # -- structural identity ------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if other is self:
            return True
        if isinstance(other, Surd):
            return self.level == other.level and self.a == other.a and self.b == other.b
        return False  # a normalised Surd is irrational, so never equals a Fraction

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.level, self.a, self.b))
        return self._hash

    # -- arithmetic ---------------------------------------------------------
    def __add__(self, other):
        return _add(self, _coerce(other))

    __radd__ = __add__

    def __sub__(self, other):
        return _add(self, _neg(_coerce(other)))

    def __rsub__(self, other):
        return _add(_coerce(other), _neg(self))

    def __mul__(self, other):
        return _mul(self, _coerce(other))

    __rmul__ = __mul__

    def __truediv__(self, other):
        return _mul(self, _inv(_coerce(other)))

    def __rtruediv__(self, other):
        return _mul(_coerce(other), _inv(self))

    def __neg__(self):
        return _neg(self)

    def __pos__(self):
        return self

    def __abs__(self):
        return self if sign(self) >= 0 else _neg(self)

    def __pow__(self, n: int):
        if n < 0:
            return _inv(self) ** (-n)
        result: Constructible = ONE
        base: Constructible = self
        while n:
            if n & 1:
                result = _mul(result, base)
            base = _mul(base, base)
            n >>= 1
        return result

    # -- ordering (exact, via sign of the difference) -----------------------
    def __lt__(self, other):
        return sign(_add(self, _neg(_coerce(other)))) < 0

    def __le__(self, other):
        return sign(_add(self, _neg(_coerce(other)))) <= 0

    def __gt__(self, other):
        return sign(_add(self, _neg(_coerce(other)))) > 0

    def __ge__(self, other):
        return sign(_add(self, _neg(_coerce(other)))) >= 0

    def __float__(self) -> float:
        return to_float(self)

    def __repr__(self) -> str:
        return fmt(self)


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _coerce(x) -> Constructible:
    if isinstance(x, (Surd, Fraction)):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        raise TypeError(
            "floats are not constructible numbers; use Fraction or int "
            "(the whole point of this kernel is that nothing is approximate)"
        )
    raise TypeError(f"cannot use {type(x).__name__} as a constructible number")


def _level(x: Constructible) -> int:
    return x.level if isinstance(x, Surd) else 0


def _tower_of(*xs: Constructible) -> Optional[Tower]:
    """The tower these operands share.

    Mixing two towers would silently reinterpret one's levels as the other's,
    so the mismatch is an error rather than a surprise several steps later.
    """
    found: Optional[Tower] = None
    for x in xs:
        if isinstance(x, Surd):
            if found is None:
                found = x.tower
            elif x.tower is not found:
                raise ValueError(
                    "these constructible numbers come from different towers; "
                    "values built in one Context cannot be combined with another's"
                )
    return found


def _split(x: Constructible, k: int) -> tuple[Constructible, Constructible]:
    """Write ``x`` as ``a + b*sqrt(r_k)`` with ``a``, ``b`` below level ``k``."""
    if isinstance(x, Surd) and x.level == k:
        return x.a, x.b
    return x, ZERO


def _norm(tower: Tower, k: int, a: Constructible, b: Constructible) -> Constructible:
    return a if is_zero(b) else Surd(tower, k, a, b)


def _add(x: Constructible, y: Constructible) -> Constructible:
    kx, ky = _level(x), _level(y)
    if kx == 0 and ky == 0:
        return x + y
    k = kx if kx > ky else ky
    tower = _tower_of(x, y)
    xa, xb = _split(x, k)
    ya, yb = _split(y, k)
    return _norm(tower, k, _add(xa, ya), _add(xb, yb))


def _neg(x: Constructible) -> Constructible:
    if isinstance(x, Surd):
        return Surd(x.tower, x.level, _neg(x.a), _neg(x.b))
    return -x


def _sub(x: Constructible, y: Constructible) -> Constructible:
    return _add(x, _neg(y))


def _mul(x: Constructible, y: Constructible) -> Constructible:
    kx, ky = _level(x), _level(y)
    if kx == 0 and ky == 0:
        return x * y
    k = kx if kx > ky else ky
    tower = _tower_of(x, y)
    r = tower.radicand(k)
    xa, xb = _split(x, k)
    ya, yb = _split(y, k)
    real = _add(_mul(xa, ya), _mul(_mul(xb, yb), r))
    surd = _add(_mul(xa, yb), _mul(xb, ya))
    return _norm(tower, k, real, surd)


def _inv(x: Constructible) -> Constructible:
    if isinstance(x, Fraction):
        if x == 0:
            raise ZeroDivisionError("division by zero in the constructible field")
        return 1 / x
    # (a + b sqrt r)^-1 = (a - b sqrt r) / (a^2 - b^2 r); the denominator is a
    # nonzero element of the field below, again by the non-square invariant.
    r = x.tower.radicand(x.level)
    denom = _sub(_mul(x.a, x.a), _mul(_mul(x.b, x.b), r))
    inv_denom = _inv(denom)
    return _norm(x.tower, x.level, _mul(x.a, inv_denom), _neg(_mul(x.b, inv_denom)))


def _div(x: Constructible, y: Constructible) -> Constructible:
    return _mul(x, _inv(y))


# ---------------------------------------------------------------------------
# public predicates and operations
# ---------------------------------------------------------------------------


def is_zero(x: Constructible) -> bool:
    """Exact zero test.  Normalised surds are irrational, hence never zero."""
    return isinstance(x, Fraction) and x == 0


def _interval(x: Constructible, prec: int) -> Interval:
    if isinstance(x, Fraction):
        return Interval.exact(x)
    memo = x.tower._interval_memo
    key = (x, prec)
    cached = memo.get(key)
    if cached is not None:
        return cached
    radicand = _interval(x.tower.radicand(x.level), prec)
    result = _interval(x.a, prec) + _interval(x.b, prec) * radicand.sqrt(prec)
    memo[key] = result
    return result


def sign(x: Constructible) -> int:
    """Exact sign: ``-1``, ``0`` or ``1``.

    The zero case is settled structurally, so the refinement loop below only
    ever runs on a value that is genuinely nonzero -- and therefore terminates.
    """
    if is_zero(x):
        return 0
    if isinstance(x, Fraction):
        return 1 if x > 0 else -1
    prec = 64
    while prec <= MAX_SIGN_PRECISION:
        enclosure = _interval(x, prec)
        if enclosure.lo > 0:
            return 1
        if enclosure.hi < 0:
            return -1
        prec *= 4
    raise ArithmeticError(  # pragma: no cover - would indicate a broken tower
        "sign() failed to converge; the tower's non-square invariant is violated"
    )


def to_float(x: Constructible, prec: int = 96) -> float:
    if isinstance(x, Fraction):
        return float(x)
    return float(_interval(x, prec).midpoint())


def _rational_sqrt(q: Fraction) -> Optional[Fraction]:
    if q < 0:
        return None
    num, den = q.numerator, q.denominator
    root_num, root_den = isqrt(num), isqrt(den)
    if root_num * root_num == num and root_den * root_den == den:
        return Fraction(root_num, root_den)
    return None


def _exact_sqrt(tower: Tower, x: Constructible, n: int) -> Optional[Constructible]:
    """Search for ``sqrt(x)`` inside the level-``n`` field, or return ``None``.

    Descent on the tower.  In ``K = F(sqrt s)`` write ``x = a + b*sqrt s``:

    * ``b == 0`` -- either ``a`` is a square in ``F``, or ``a/s`` is (giving
      ``sqrt x = sqrt(a/s) * sqrt s``).  This is what collapses ``sqrt 8``
      inside ``Q(sqrt 2)`` to ``2*sqrt 2`` instead of stacking a new level.
    * ``b != 0`` -- if ``sqrt x = u + v*sqrt s`` then ``u^2 + v^2 s = a`` and
      ``2uv = b``, so ``u^2`` solves a quadratic over ``F``: we need
      ``d = a^2 - b^2 s`` to be a square ``e^2`` in ``F``, and then one of
      ``(a +- e)/2`` to be a square ``u^2`` in ``F``; ``v = b/(2u)``.
    """
    key = (x, n)
    memo = tower._sqrt_memo
    if key in memo:
        return memo[key]
    result = _exact_sqrt_uncached(tower, x, n)
    memo[key] = result
    return result


def _exact_sqrt_uncached(tower: Tower, x: Constructible, n: int) -> Optional[Constructible]:
    if is_zero(x):
        return ZERO
    if n == 0:
        return _rational_sqrt(x) if isinstance(x, Fraction) else None

    s = tower.radicand(n)
    a, b = _split(x, n)

    if is_zero(b):
        root = _exact_sqrt(tower, a, n - 1)
        if root is not None:
            return root
        root = _exact_sqrt(tower, _div(a, s), n - 1)
        if root is not None:
            return _norm(tower, n, ZERO, root)
        return None

    d = _sub(_mul(a, a), _mul(_mul(b, b), s))
    e = _exact_sqrt(tower, d, n - 1)
    if e is None:
        return None
    for t in (_mul(_add(a, e), HALF), _mul(_sub(a, e), HALF)):
        u = _exact_sqrt(tower, t, n - 1)
        if u is not None and not is_zero(u):
            return _norm(tower, n, u, _div(b, _mul(u, 2)))
    return None


def sqrt(x, tower: Optional[Tower] = None) -> Constructible:
    """Exact square root, reusing the tower when possible and extending when not."""
    x = _coerce(x)
    if is_zero(x):
        return ZERO
    if tower is None:
        tower = _tower_of(x) or current_tower()
    elif isinstance(x, Surd) and x.tower is not tower:
        raise ValueError("constructible number belongs to a different tower")
    if sign(x) < 0:
        raise ValueError(f"sqrt of a negative magnitude: {fmt(x)}")
    found = _exact_sqrt(tower, x, tower.depth)
    if found is not None:
        # Both roots satisfy the recursion, and the descent may well surface the
        # negative one; a magnitude must come back non-negative.
        return found if sign(found) >= 0 else _neg(found)
    return tower.extend(x)


def fmt(x: Constructible) -> str:
    """A readable rendering such as ``1/2 + 1/2*sqrt(5)``."""
    if isinstance(x, Fraction):
        return str(x)
    root = f"sqrt({fmt(x.tower.radicand(x.level))})"
    coefficient, joiner = x.b, "+"
    if isinstance(coefficient, Fraction) and coefficient < 0:
        coefficient, joiner = -coefficient, "-"
    if isinstance(coefficient, Surd):
        body = f"({fmt(coefficient)})*{root}"
    elif coefficient == ONE:
        body = root
    else:
        body = f"{fmt(coefficient)}*{root}"
    if is_zero(x.a):
        return body if joiner == "+" else f"-{body}"
    return f"{fmt(x.a)} {joiner} {body}"


# ---------------------------------------------------------------------------
# ambient context
# ---------------------------------------------------------------------------

_STACK: list["Context"] = []
_DEFAULT: Optional["Context"] = None


class Context:
    """A scope owning one tower.

    Every proposition runs inside its own context so tower depth stays bounded
    by the length of a single construction rather than growing across a whole
    session.  Nested propositions share their caller's context, which is what
    lets one construction's output feed another's input.
    """

    __slots__ = ("tower", "label")

    def __init__(self, label: str = "", tower: Optional[Tower] = None) -> None:
        # An inherited tower lets a caller feed values it already built into a
        # proposition; a fresh one keeps unrelated constructions from piling up
        # levels on each other.
        self.tower = tower if tower is not None else Tower()
        self.label = label

    def __enter__(self) -> "Context":
        _STACK.append(self)
        return self

    def __exit__(self, *exc) -> bool:
        _STACK.pop()
        return False

    def sqrt(self, x) -> Constructible:
        return sqrt(x, self.tower)


def active_context() -> Optional[Context]:
    """The innermost open context, or ``None`` -- without creating one."""
    return _STACK[-1] if _STACK else None


def current_context() -> Context:
    global _DEFAULT
    if _STACK:
        return _STACK[-1]
    if _DEFAULT is None:
        _DEFAULT = Context("default")
    return _DEFAULT


def current_tower() -> Tower:
    return current_context().tower
