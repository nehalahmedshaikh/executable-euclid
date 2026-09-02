"""Which of Euclid's stated hypotheses the conclusions turn out not to need.

A proposition says nothing about configurations its hypotheses exclude, so
ordinarily an excluded configuration is thrown away.  That makes one question
unaskable: *would the conclusion have held anyway?*  Lifting the exclusion makes
it askable.

The method:

1. take a configuration the proposition's own sampler accepts;
2. bend one given -- :mod:`euclid.measure.bend` holds the vocabulary -- so that
   something about it stops being true;
3. run with hypotheses recorded rather than enforced;
4. see what happened.

Four outcomes, and they mean different things:

``needed``
    one of the proposition's own claims failed.  The hypothesis was holding the
    conclusion up.
``well-definedness``
    the construction itself broke -- two circles stopped meeting, a line became
    a point.  The hypothesis is keeping the construction possible rather than
    the conclusion true, which is a weaker and less interesting kind of
    necessity, so it is reported apart.
``survived``
    everything still held.  A *candidate* for a hypothesis Euclid states but the
    conclusion does not require.
``implied``
    no configuration broke this hypothesis and left the others standing, so
    there is nothing to attribute an outcome to.  A hypothesis the others entail
    cannot be broken alone, and that is a result rather than a failure to look:
    I.4's ``AC = DF`` goes this way, because every bend that breaks it breaks
    ``AB = DE`` with it.  Reported as evidence of the same kind as a candidate,
    and graded the same way -- the search cycles the bend plan systematically,
    but it is bounded, and it does not solve for a separating figure.

Two figures are published rather than one.  Every stated hypothesis carries a
verdict, and beside that stands the share for which a separating configuration
was actually found; quoting only the first would let ``implied`` pass for
``needed``.

Two disciplines keep this honest.  A run in which more than one of *this*
proposition's hypotheses broke is discarded, because the outcome cannot be
attributed to either.  And a candidate is never reported as a result: it is
reported as a candidate, with the number of configurations behind it, because
"no counterexample was found among the ones tried" is not "there is none".

A proposition this one appeals to may fail on the bent figure while the
conclusion holds -- II.9's does, every time, because the bend destroys the
betweenness I.47 needs.  That is counted and reported, and it does not make the
hypothesis needed: what it says is that the argument stopped going through,
which is not the question.

The likeliest explanation for a surviving hypothesis is that the proposition's
claims are too weak to notice the difference -- not that Euclid was redundant.
Read the claims before believing the verdict.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..elements.registry import Proposition, all_propositions
from .sweep import bend_sweep, ran_every_trial

__all__ = ["Necessity", "hypothesis_necessity", "necessity_report"]

NEEDED = "needed"
WELL_DEFINED = "well-definedness"
SURVIVED = "survived"
IMPLIED = "implied"


@dataclass
class Necessity:
    """What happened to one hypothesis when it was broken."""

    ref: str
    text: str
    guard: bool = False        # our own well-formedness, not Euclid's condition
    broken: int = 0            # runs where this was the only hypothesis violated
    needed: int = 0            # ...and a claim then failed
    well_defined: int = 0      # ...and the construction broke instead
    survived: int = 0          # ...and everything still held
    appeals_failed: int = 0    # ...in this many, a proposition it cites did not

    @property
    def verdict(self) -> str:
        """Needed beats survived beats well-definedness, in that order.

        One refutation settles it: the conclusion is false somewhere the
        hypothesis is broken, so the hypothesis was holding it up.  Failing that,
        one configuration where the hypothesis was broken and the conclusion held
        is a witness, and a run where the construction gave out is not evidence
        against it -- it is not evidence about the conclusion at all.  Survived
        used to be reported only when *no* run had collapsed, which let a bend
        that went too far cancel a witness that had not.
        """
        if self.needed:
            return NEEDED
        if self.survived:
            return SURVIVED
        if self.well_defined:
            return WELL_DEFINED
        # No bend of the figure broke this hypothesis and left the others
        # standing. The likeliest reason is that the others entail it -- a
        # redundant hypothesis, which is a result. It was filed as ignorance
        # before, and it is the difference between judging 54% of what Euclid
        # states and judging all of it. Evidence of the same kind as a
        # candidate, and graded the same way: no separating configuration was
        # found among the ones tried, which is not "there is none".
        return IMPLIED

    def __str__(self) -> str:
        return (f"{self.ref:<8} {self.verdict:<16} "
                f"({self.survived}/{self.broken} configurations)  {self.text}")


_TALLY = {NEEDED: "needed", WELL_DEFINED: "well_defined", SURVIVED: "survived"}



def hypothesis_necessity(
    entry: Proposition, trials: int = 24, seed: int = 0
) -> list[Necessity]:
    """Break each hypothesis of one proposition in turn and see what follows."""
    found: dict[str, Necessity] = {}
    for seen in bend_sweep(entry, trials=trials, seed=seed, tag="necessity"):
        if not seen.bent:
            # The unbent run is the inventory: every hypothesis the proposition
            # states, so that one no bend could isolate is reported rather than
            # missing.
            for stated in seen.hypotheses:
                found.setdefault(stated.text, Necessity(
                    entry.ref, stated.text, guard=stated.detail == "guard"))
            continue
        # Only a run that broke exactly one of *this* proposition's hypotheses
        # says anything about that hypothesis; with two broken the outcome
        # cannot be attributed to either.
        #
        # Hypotheses broken further down are not counted. A proposition carried
        # out on a bent figure hands that figure to the propositions it appeals
        # to, and theirs break as a consequence of the one bend rather than
        # beside it. Counting them discarded almost every run that reached an
        # appeal at all -- which, once a false claim stopped ending the run, was
        # nearly every run that had anything to say. I.5 lost its verdict that
        # way: the runs where AB = AC broke were exactly the runs that went on to
        # break I.4's hypotheses, and every one of them was thrown out.
        mine = [(text, guard) for ref, text, guard in seen.violations
                if ref == entry.ref]
        if len({text for text, _ in mine}) != 1:
            continue
        # A refuted claim outranks a collapsed construction: the conclusion was
        # false before the figure gave out, which is what the hypothesis was for.
        outcome = (NEEDED if seen.refuted
                   else WELL_DEFINED if seen.collapsed else SURVIVED)
        text, is_guard = mine[0]
        record = found.setdefault(text, Necessity(entry.ref, text, guard=is_guard))
        record.broken += 1
        setattr(record, _TALLY[outcome], getattr(record, _TALLY[outcome]) + 1)
        # A failed appeal does not change the verdict. The question is whether
        # the conclusion held, and it did; what broke was a proposition this one
        # cites, on a figure it was never about. But it is worth counting, and it
        # sharpens the standing caveat about candidates: where the appeals failed
        # and the conclusion did not, the conclusion is the weaker statement.
        record.appeals_failed += int(seen.appeal_failed)
    return sorted(found.values(), key=lambda item: item.text)


@dataclass
class NecessityReport:
    """The corpus-wide picture, with its own coverage stated."""

    results: list[Necessity] = field(default_factory=list)
    propositions_tried: int = 0
    hypotheses_total: int = 0
    truncated: list[str] = field(default_factory=list)  # ran out of budget

    @property
    def tested(self) -> list[Necessity]:
        """Hypotheses a separating configuration was actually found for."""
        return [item for item in self.results if item.broken]

    @property
    def implied(self) -> list[Necessity]:
        """Hypotheses no bend could break while leaving the others standing.

        Read as candidates for redundancy, on the same footing as a surviving
        hypothesis: the search was systematic but bounded, and it cycles the
        bend plan rather than solving for a separating figure.
        """
        return [item for item in self.results if item.verdict == IMPLIED]

    @property
    def candidates(self) -> list[Necessity]:
        """Euclid's hypotheses that were broken and whose conclusions held anyway.

        Guards are left out.  Breaking "the ratio is not 1" and finding the
        conclusion intact says something about our input handling, and standing
        it beside a real surviving hypothesis made the count read as much more
        than it was.
        """
        return [item for item in self.tested
                if item.verdict == SURVIVED and not item.guard]

    @property
    def surviving_guards(self) -> list[Necessity]:
        """Well-formedness conditions of our own that the code tolerates."""
        return [item for item in self.tested
                if item.verdict == SURVIVED and item.guard]

    @property
    def coverage(self) -> float:
        """The share of stated hypotheses carrying a verdict, which is all of them."""
        if not self.hypotheses_total:
            return 0.0
        return (len(self.tested) + len(self.implied)) / self.hypotheses_total

    @property
    def separated(self) -> float:
        """...and the share a separating configuration was found for."""
        if not self.hypotheses_total:
            return 0.0
        return len(self.tested) / self.hypotheses_total

    def summary(self) -> str:
        counts = defaultdict(int)
        for item in self.tested:
            counts[item.verdict] += 1
        return (
            f"{self.propositions_tried} propositions, "
            f"{self.hypotheses_total} hypotheses stated, all of them judged "
            f"({100 * self.coverage:.0f}% coverage); "
            f"{len(self.tested)} by a configuration that broke it alone "
            f"({100 * self.separated:.0f}%)\n"
            f"  needed             : {counts[NEEDED]}\n"
            f"  keeps construction : {counts[WELL_DEFINED]}\n"
            f"  survived breaking  : {len(self.candidates)}  <- candidates, not results\n"
            f"  our own guards     : {len(self.surviving_guards)}  "
            "(well-formedness we added, tolerated by the code)\n"
            f"  implied            : {len(self.implied)}  "
            "<- no bend broke it alone; the other hypotheses may entail it\n"
            f"  short of the trials: {len(self.truncated)}  "
            "propositions too slow to bend the full number of times"
        )


def necessity_report(entries=None, trials: int = 24) -> NecessityReport:
    """Run the analysis over the corpus."""
    chosen = list(entries) if entries is not None else all_propositions()
    report = NecessityReport()
    for entry in chosen:
        if entry.sample is None:
            continue
        report.propositions_tried += 1
        found = hypothesis_necessity(entry, trials=trials)
        # Every hypothesis the proposition states is in the inventory, so the
        # total is read off it rather than counted by a second set of runs.
        report.hypotheses_total += len(found)
        report.results.extend(found)
        if not ran_every_trial(entry.ref):
            report.truncated.append(entry.ref)
    return report
