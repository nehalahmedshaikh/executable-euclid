"""What the corpus can be asked, now that all of it runs.

These are questions about the *Elements* that need an exact, executable, complete
text to answer, and which the text alone cannot settle:

* :mod:`depth` -- how algebraically deep each proposition goes, and where in the
  book each degree first becomes necessary;
* :mod:`gaps` -- where Book X's taxonomy of irrationals stops naming things;
* :mod:`necessity` -- which of Euclid's stated hypotheses the conclusions turn
  out not to need.

Each reports its own method and coverage; a number without those is not a
finding.
"""

from .depth import Depth, algebraic_depth, ceilings, depth_profile, first_appearances
from .gaps import Gap, simplest_gap, taxonomy_gaps
from .necessity import Necessity, hypothesis_necessity, necessity_report
from .record import FINDINGS_PATH, load_findings, write_findings

__all__ = [
    "Depth",
    "Gap",
    "FINDINGS_PATH",
    "Necessity",
    "algebraic_depth",
    "ceilings",
    "depth_profile",
    "first_appearances",
    "hypothesis_necessity",
    "load_findings",
    "necessity_report",
    "simplest_gap",
    "taxonomy_gaps",
    "write_findings",
]
