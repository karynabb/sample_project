from enum import Enum
from typing import TYPE_CHECKING

from .base_validator import CandidateValidator

if TYPE_CHECKING:
    from app.algorithm.models import NameCandidate


class PathwayType(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    COINED = "coined"


class MaxPathwayTypeValidator(CandidateValidator):
    """
    Checks that there are no more than a given number of candidates
    for a given pathway type in a batch.
    """

    def __init__(self, max_candidates: int, pathway_type: PathwayType) -> None:
        self.max_candidates = max_candidates
        self.pathway_type = pathway_type
        self._current_amount = 0

    def validate(self, candidate: "NameCandidate") -> bool:
        if not candidate.pathway.code.startswith(self.pathway_type.value):
            # Don't check candidates from a different pathway type
            return True

        if self._current_amount >= self.max_candidates:
            return False
        self._current_amount += 1
        return True

    def reset(self) -> None:
        self._current_amount = 0
