"""The corpus: Euclid's propositions as executable, self-checking programs.

Importing this package registers every proposition the machine knows.
"""

from . import book01_foundations  # noqa: F401  (import registers the propositions)
from . import book01_parallels  # noqa: F401
from . import book02  # noqa: F401
from . import book03  # noqa: F401
from . import book04  # noqa: F401
from . import book05  # noqa: F401
from . import book06  # noqa: F401
from . import book07  # noqa: F401
from . import book08  # noqa: F401
from . import book09  # noqa: F401
from . import book10  # noqa: F401
from . import book11  # noqa: F401
from . import book13  # noqa: F401
from .registry import (
    BOOK_TITLES,
    CONSTRUCTION,
    THEOREM,
    BadConfiguration,
    Out,
    ProofFailure,
    Proposition,
    Run,
    all_propositions,
    claim,
    get,
    hypothesis,
    proposition,
    reference_kind,
    run,
    run_sampled,
)

__all__ = [
    "BOOK_TITLES",
    "BadConfiguration",
    "CONSTRUCTION",
    "Out",
    "ProofFailure",
    "Proposition",
    "Run",
    "THEOREM",
    "all_propositions",
    "claim",
    "get",
    "hypothesis",
    "proposition",
    "reference_kind",
    "run",
    "run_sampled",
]
