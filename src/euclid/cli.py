"""``euclid`` -- the command line."""

from __future__ import annotations

import argparse
import os
import sys
from fractions import Fraction
from pathlib import Path

from . import __version__


def _load():
    from . import elements  # noqa: F401  registers the corpus
    from .graph import build

    return build()


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def cmd_list(args) -> int:
    from .elements.registry import BOOK_TITLES, all_propositions

    current = None
    for entry in all_propositions():
        if args.book and entry.book != args.book:
            continue
        if entry.book != current:
            current = entry.book
            print(f"\nBook {current} -- {BOOK_TITLES.get(current, '')}")
        print(f"  {entry.ref:<8} {entry.statement[:82]}")
    return 0


def cmd_run(args) -> int:
    import random

    from .elements.registry import get, run_sampled
    from .render.svg import render_trace

    entry = get(args.ref)
    rng = random.Random(args.seed)
    # A sampler is allowed to draw a configuration its own proposition rejects;
    # the fuzzer counts those and moves on. This did the same as `verify` only
    # by luck, and failed outright on the first draw IX.30 turned down.
    from .elements.registry import BadConfiguration

    for attempt in range(40):
        try:
            result = run_sampled(args.ref, rng)
            break
        except BadConfiguration:
            if attempt == 39:
                raise
    print(f"{entry.ref}  {entry.statement}")
    print("        (Heath, 1908)\n")
    if entry.note:
        print(f"  {entry.note}\n")
    for claim in result.trace.claims:
        marker = "given " if claim.by == ("hypothesis",) else "step  "
        citation = "" if claim.by == ("hypothesis",) else f"   [{', '.join(claim.by)}]"
        print(f"  {marker} {claim.text}{citation}")
    print(f"\n  {result.trace.step_count} straightedge-and-compass moves, "
          f"{len(result.trace.claims)} claims, all verified exactly.")
    if args.svg:
        Path(args.svg).write_text(render_trace(result.trace, entry.ref), encoding="utf-8")
        print(f"  diagram written to {args.svg}")
    return 0


def cmd_why(args) -> int:
    graph = _load()
    if args.ref not in graph.nodes:
        print(f"no such proposition: {args.ref}", file=sys.stderr)
        return 1
    entry = graph.nodes[args.ref]
    print(f"{entry.ref}  {entry.statement}\n")
    chain = graph.tree_shake(args.ref)
    print(f"  rests on {len(chain) - 1} earlier propositions, "
          f"{graph.depth(args.ref)} layers deep\n")
    for ref in chain:
        needs = sorted(graph.needs(ref))
        arrow = f"  <- {', '.join(needs)}" if needs else ""
        marker = "*" if ref == args.ref else " "
        print(f"  {marker} {ref:<8}{arrow}")
    axioms = sorted(graph.axioms(args.ref))
    print(f"\n  first principles: {', '.join(axioms) or 'none recorded'}")
    print(f"  parallel postulate: "
          f"{'required' if graph.uses_parallel_postulate(args.ref) else 'not required'}")
    return 0


def cmd_minimal(args) -> int:
    graph = _load()
    if args.ref not in graph.nodes:
        print(f"no such proposition: {args.ref}", file=sys.stderr)
        return 1
    chain = graph.tree_shake(args.ref)
    dropped = len(graph.nodes) - len(chain)
    print(f"The minimal Elements for {args.ref}: {len(chain)} propositions "
          f"({dropped} of {len(graph.nodes)} dropped)\n")
    for index, ref in enumerate(chain, 1):
        print(f"  {index:>3}. {ref:<8} {graph.nodes[ref].statement[:76]}")
    return 0


def cmd_verify(args) -> int:
    from .elements.registry import all_propositions
    from .verify import certify

    chosen = [e for e in all_propositions() if not args.book or e.book == args.book]
    failures = 0
    for entry in chosen:
        report = certify(entry.ref, trials=args.trials)
        print("  " + report.line())
        failures += len(report.failures)
        for failure in report.failures[:2]:
            print(f"         {failure.kind}: {failure.message[:110]}")
    print(f"\n  {len(chosen)} propositions, {failures} failures")
    return 1 if failures else 0


def cmd_ledger(args) -> int:
    from .elements.registry import all_propositions
    from .verify import audit

    if args.ref:
        print(audit(args.ref, trials=args.trials).report())
        return 0
    chosen = [e for e in all_propositions() if not args.book or e.book == args.book]
    print(f"  {'ref':<8} {'continuity':>10} {'order':>6} {'case':>5}")
    totals = [0, 0, 0]
    for entry in chosen:
        led = audit(entry.ref, trials=args.trials)
        counts = (led.continuity_debt, len(led.of_kind("order")), len(led.of_kind("case")))
        totals = [t + c for t, c in zip(totals, counts)]
        print(f"  {entry.ref:<8} {counts[0]:>10} {counts[1]:>6} {counts[2]:>5}")
    print(f"\n  totals: {totals[0]} unjustified intersections, {totals[1]} order facts, "
          f"{totals[2]} configuration-dependent steps")
    return 0


def cmd_optimize(args) -> int:
    from .search import PROBLEMS, solve

    if args.problem not in PROBLEMS:
        print("known problems:", ", ".join(sorted(PROBLEMS)), file=sys.stderr)
        return 1
    result = solve(
        args.problem, isa=args.isa, max_depth=args.depth, node_budget=args.budget
    )
    print(result.report())
    problem = PROBLEMS[args.problem]
    if problem.euclid:
        import random

        from .elements.registry import run_sampled

        try:
            trace = run_sampled(problem.euclid, random.Random(3)).trace
            print(f"\n  Euclid solves this in {problem.euclid}, "
                  f"drawing {trace.step_count} lines and circles.")
        except Exception:  # pragma: no cover - comparison is a nicety
            pass
    return 0


def cmd_ngon(args) -> int:
    from .kernel.minpoly import ngon_verdict

    print(ngon_verdict(args.n).report())
    return 0


def cmd_impossible(args) -> int:
    from .kernel.minpoly import (
        cube_duplication_verdict,
        heptagon_verdict,
        trisection_verdict,
    )

    for verdict in (trisection_verdict(), cube_duplication_verdict(), heptagon_verdict()):
        print(verdict.report())
        print()
    return 0


def _parse_magnitude(text: str):
    """Read a magnitude such as ``(1+sqrt(5))/2`` into an exact kernel value."""
    from .kernel.field import sqrt

    allowed = {"sqrt": sqrt, "Fraction": Fraction, "__builtins__": {}}
    cleaned = text.replace("^", "**")
    try:
        value = eval(cleaned, allowed, {})  # noqa: S307 - a closed namespace
    except Exception as exc:
        raise ValueError(f"could not read the magnitude {text!r}: {exc}") from exc
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        raise ValueError("magnitudes must be exact; write sqrt(2), not 1.414")
    return value


def cmd_classify(args) -> int:
    from .elements.book10 import classify
    from .kernel.field import Context

    with Context("classify"):
        try:
            value = _parse_magnitude(args.magnitude)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(classify(value).report())
    return 0


def cmd_measure(args) -> int:
    """Questions the corpus can be asked, now that all of it runs."""
    from .elements.registry import BOOK_ORDER
    from .measure import ceilings, depth_profile, first_appearances, necessity_report

    if args.write:
        from .measure import FINDINGS_PATH, write_findings
        from .measure.record import RECORDED_TRIALS

        strength = args.trials if args.trials is not None else RECORDED_TRIALS
        print(
            f"running the corpus at {strength} trials on {args.jobs} "
            f"{'process' if args.jobs == 1 else 'processes'}"
        )
        payload = write_findings(
            trials=strength, jobs=args.jobs,
            progress=lambda stage: print(f"finished: {stage}", flush=True),
            resume=args.resume,
        )
        print(f"wrote {FINDINGS_PATH.name}: {payload['corpus']} propositions measured")
        return 0

    if not (args.depth or args.needless or args.fields or args.unfalsified):
        print("choose --depth, --needless, --fields, --unfalsified or --write",
              file=sys.stderr)
        return 1

    if args.depth:
        profile = depth_profile()
        print("The algebraic degree each book reaches\n")
        for book, top in sorted(ceilings(profile).items(),
                                key=lambda item: BOOK_ORDER.index(item[0])):
            print(f"  {book:<5} {top}")
        print("\nWhere each degree is first needed\n")
        for order, ref in first_appearances(profile).items():
            print(f"  degree {order:<3} {ref:<8} {profile[ref].where}")

    if args.fields:
        from .measure.fields import partition

        found = partition(trials=8)
        counts = {name: len(refs) for name, refs in found["buckets"].items()}
        print("Restricting the field, and what each rung buys\n")
        print(f"  complete over Q                {counts['rational']:>4}")
        print(f"  need a length measured         {counts['measuring_only']:>4}"
              "   (Q^pyth is enough, and they cross no circle)")
        print(f"  need two circles to meet       {counts['needs_continuity']:>4}")
        print(f"  are about an irrational        {counts['needs_magnitude']:>4}")
        print(f"  vary by configuration          {counts['configuration_dependent']:>4}")
        print(f"  no rational configuration      {counts['untestable']:>4}   (untestable)")
        lucky = found["buckets"]["discharged_luckily"]
        if lucky:
            print(f"\n  {len(lucky)} pass over Q^pyth while carrying continuity debt:")
            print(f"    {', '.join(sorted(lucky))}")
            print("    their circles meet where the sampled configuration already was,")
            print("    so the gain is about the sampler.")
        for ref in ("I.1", "I.20"):
            verdict = found["rational"].get(ref)
            if verdict is not None and verdict.cause:
                print(f"\n  {ref}: {verdict.cause} at {verdict.site}"
                      f" -- wants sqrt({verdict.radicand})")

    if args.needless:
        report = necessity_report(trials=args.trials if args.trials is not None else 16)
        print("\nHypotheses, broken one at a time\n")
        print(report.summary())
        print("\n  Candidates are configurations where the hypothesis was broken and")
        print("  every claim still held. That is evidence, not proof: the likeliest")
        print("  reading of a candidate is that the claims are too weak to notice.\n")
        for item in sorted(report.candidates, key=lambda x: -x.broken)[:20]:
            print(f"    {item.ref:<8} x{item.broken:<3} {item.text}")

    if args.unfalsified:
        from .measure.mutation import mutation_report

        report = mutation_report(trials=args.trials if args.trials is not None else 16)
        print("\nClaims, with the figure beneath them bent\n")
        print(report.summary())
        print("\n  An unfalsified claim is one no bend made false. That can mean it")
        print("  asserts nothing, or that the bends never reached what it is about,")
        print("  or that it is genuinely insensitive to the given that moved.\n")
        for item in sorted(report.unfalsified, key=lambda x: (x.ref, x.text))[:40]:
            print(f"    {item.ref:<9} {item.text[:66]}")
    return 0


def cmd_gap(args) -> int:
    """Constructible numbers Book X's thirteen species do not name."""
    from .measure import simplest_gap, taxonomy_gaps

    if args.all:
        found = taxonomy_gaps(limit=10)
        if not found:
            print("every candidate tried falls inside the thirteen species")
            return 0
        print(f"{len(found)} constructible numbers Book X has no name for:\n")
        for gap in found:
            print(f"  {gap.expression:<26} degree {gap.degree:<3} ~ {gap.value_float:.8f}")
        return 0

    gap = simplest_gap()
    if gap is None:
        print("every candidate tried falls inside the thirteen species")
        return 0
    print("The simplest constructible number Book X cannot name\n")
    print(gap)
    return 0


def cmd_site(args) -> int:
    from .render.site import build as build_site

    destination = Path(args.out)
    written = build_site(destination, run_search=not args.no_search)
    print(f"  wrote {len(written)} pages to {destination}")
    print(f"  open {destination / 'index.html'}")
    return 0


# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="euclid",
        description="Euclid's Elements as executable, exactly-verified software.",
    )
    parser.add_argument("--version", action="version", version=f"euclid-machine {__version__}")
    subs = parser.add_subparsers(dest="command", required=True)

    p = subs.add_parser("list", help="list the encoded propositions")
    p.add_argument("book", nargs="?", help="restrict to one book, e.g. I")
    p.set_defaults(func=cmd_list)

    p = subs.add_parser("run", help="construct and verify one proposition")
    p.add_argument("ref", help="e.g. I.47")
    p.add_argument("--seed", type=int, default=3)
    p.add_argument("--svg", help="also write the diagram to this file")
    p.set_defaults(func=cmd_run)

    p = subs.add_parser("why", help="show what a proposition depends on")
    p.add_argument("ref")
    p.set_defaults(func=cmd_why)

    p = subs.add_parser("minimal", help="the minimal Elements needed for a proposition")
    p.add_argument("ref")
    p.set_defaults(func=cmd_minimal)

    p = subs.add_parser("verify", help="certify propositions over random configurations")
    p.add_argument("book", nargs="?")
    p.add_argument("--trials", type=int, default=12)
    p.set_defaults(func=cmd_verify)

    p = subs.add_parser("ledger", help="what the propositions take on trust")
    p.add_argument("ref", nargs="?")
    p.add_argument("--book")
    p.add_argument("--trials", type=int, default=8)
    p.set_defaults(func=cmd_ledger)

    p = subs.add_parser("optimize", help="search for the shortest construction")
    p.add_argument("problem")
    p.add_argument("--isa", default="full",
                   choices=["full", "compass-only", "straightedge-only", "rusty-compass"])
    p.add_argument("--depth", type=int, default=5)
    p.add_argument("--budget", type=int, default=400_000)
    p.set_defaults(func=cmd_optimize)

    p = subs.add_parser("ngon", help="is the regular n-gon constructible?")
    p.add_argument("n", type=int)
    p.set_defaults(func=cmd_ngon)

    p = subs.add_parser("impossible", help="the three classical impossibilities")
    p.set_defaults(func=cmd_impossible)

    p = subs.add_parser("classify", help="name a magnitude in Book X's vocabulary")
    p.add_argument("magnitude", help='e.g. "sqrt(3)+sqrt(5)" or "(1+sqrt(5))/2"')
    p.set_defaults(func=cmd_classify)

    p = subs.add_parser("measure", help="ask the corpus about itself")
    p.add_argument("--depth", action="store_true",
                   help="the algebraic degree each proposition reaches")
    p.add_argument("--needless", action="store_true",
                   help="hypotheses the conclusions turn out not to need")
    p.add_argument("--fields", action="store_true",
                   help="which propositions survive a smaller number field")
    p.add_argument("--unfalsified", action="store_true",
                   help="claims no bend of the figure beneath them made false")
    p.add_argument("--write", action="store_true",
                   help="recompute and record findings.json, which the site reads")
    p.add_argument("--trials", type=int, default=None,
                   help="how hard to try; --write records at 48 unless told otherwise")
    p.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1),
                   help="parallel processes for --write (default: up to 4)")
    p.add_argument("--resume", action="store_true",
                   help="reuse completed stages from an interrupted --write")
    p.set_defaults(func=cmd_measure)

    p = subs.add_parser("gap", help="constructible numbers Book X cannot name")
    p.add_argument("--all", action="store_true", help="list more than the simplest")
    p.set_defaults(func=cmd_gap)

    p = subs.add_parser("site", help="generate the static site")
    p.add_argument("--out", default="docs")
    p.add_argument("--no-search", action="store_true",
                   help="leave the recorded construction searches off the pages")
    p.set_defaults(func=cmd_site)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
