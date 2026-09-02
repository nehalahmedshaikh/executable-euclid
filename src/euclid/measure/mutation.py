"""Which claims would notice if the figure were wrong.

A claim that cannot come out false is not a check, and the corpus has had three
of them that every test passed.  ``test_no_claim_is_incapable_of_failing`` reads
the source for the two shapes that were caught by eye -- a literal, and a
comparison whose two sides unparse alike -- and that is as far as reading the
source can go.  It sees ``x == x``.  It does not see

.. code-block:: python

    area = compound
    claim("...", "X.20", area == compound * 1)

which is the same assertion wearing a second name, nor a claim about a quantity
that happens to be equal for a reason having nothing to do with the proposition.
Both certify perfectly and check nothing.

So instead of reading the claim, bend the figure underneath it and watch.  Take
a configuration the sampler accepts, perturb one given
(:mod:`euclid.measure.bend`), and run with hypotheses recorded rather than
enforced and with a false claim noted rather than raised, so that one run judges
every claim the proposition makes.  A claim that comes out false on some bent
figure is doing work.  A claim true on every one of them is *unfalsified*, and
wants reading.

Unfalsified is not the same as vacuous, and the difference is the whole reason
this is a measurement and not a verdict.  A claim can survive every bend because
it asserts nothing; or because the bends available to this proposition never
reach the thing it is about; or because it is genuinely insensitive to the given
that moved.  What the analysis produces is a list to read, and the residue that
survives reading is recorded rather than rounded away.

Claims cited to ``hypothesis`` are left out.  Those are the proposition's
contract, not its proof, and :mod:`euclid.measure.necessity` is the analysis
that judges them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..elements.registry import Proposition, all_propositions
from .sweep import bend_sweep, ran_every_trial

__all__ = [
    "Mutation",
    "MutationReport",
    "claim_mutation",
    "mutation_report",
]


LIVE = "live"
UNFALSIFIED = "unfalsified"
UNREACHED = "unreached"


@dataclass
class Mutation:
    """What happened to one claim when the figure beneath it was bent."""

    ref: str
    text: str
    by: tuple[str, ...] = ()
    reached: int = 0           # bent runs that got as far as stating it
    broke: int = 0             # ...and it came out false

    @property
    def verdict(self) -> str:
        if self.broke:
            return LIVE
        if self.reached:
            return UNFALSIFIED
        return UNREACHED

    def __str__(self) -> str:
        return (f"{self.ref:<9} {self.verdict:<12} "
                f"({self.broke}/{self.reached} bends)  {self.text}")


def claim_mutation(
    entry: Proposition, trials: int = 24, seed: int = 0
) -> list[Mutation]:
    """Bend one proposition's figure repeatedly and see which claims notice."""
    found: dict[str, Mutation] = {}
    for seen in bend_sweep(entry, trials=trials, seed=seed, tag="mutation"):
        # A bend can break the construction long before a claim is reached. The
        # claims that were reached still count; the rest are not evidence from
        # this run either way.
        for claim in seen.own:
            record = found.setdefault(
                claim.text, Mutation(entry.ref, claim.text, tuple(claim.by)))
            record.reached += int(seen.bent)
            record.broke += int(seen.bent and not claim.holds)
    return sorted(found.values(), key=lambda item: item.text)


@dataclass
class MutationReport:
    """The corpus-wide picture, with its own coverage stated."""

    results: list[Mutation] = field(default_factory=list)
    propositions_tried: int = 0
    truncated: list[str] = field(default_factory=list)  # ran out of budget

    @property
    def claims_total(self) -> int:
        return len(self.results)

    @property
    def live(self) -> list[Mutation]:
        return [item for item in self.results if item.verdict == LIVE]

    @property
    def unfalsified(self) -> list[Mutation]:
        """Claims no bend of the figure made false.  A list to read."""
        return [item for item in self.results if item.verdict == UNFALSIFIED]

    @property
    def unreached(self) -> list[Mutation]:
        """Claims no bent run got as far as stating: no evidence either way."""
        return [item for item in self.results if item.verdict == UNREACHED]

    @property
    def coverage(self) -> float:
        if not self.claims_total:
            return 0.0
        return len(self.live) / self.claims_total

    def summary(self) -> str:
        return (
            f"{self.propositions_tried} propositions, "
            f"{self.claims_total} claims stated, "
            f"{len(self.live)} of them broken by some bend of the figure "
            f"({100 * self.coverage:.0f}% coverage)\n"
            f"  live         : {len(self.live)}\n"
            f"  unfalsified  : {len(self.unfalsified)}  <- read these\n"
            f"  unreached    : {len(self.unreached)}  "
            "(no bent run stated them; no evidence either way)\n"
            f"  short of the trials: {len(self.truncated)}  "
            "propositions too slow to bend the full number of times"
        )


def mutation_report(entries=None, trials: int = 24) -> MutationReport:
    """Run the analysis over the corpus."""
    chosen = list(entries) if entries is not None else all_propositions()
    report = MutationReport()
    for entry in chosen:
        if entry.sample is None:
            continue
        report.propositions_tried += 1
        report.results.extend(claim_mutation(entry, trials=trials))
        # Fewer bends behind a verdict is weaker evidence, and unfalsified is the
        # verdict a shortage of bends produces. Naming the propositions that ran
        # short is what keeps the two apart.
        if not ran_every_trial(entry.ref):
            report.truncated.append(entry.ref)
    return report
