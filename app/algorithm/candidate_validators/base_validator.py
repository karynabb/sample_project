from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.algorithm.models import NameCandidate


class CandidateValidator(ABC):
    @abstractmethod
    def validate(self, candidate: "NameCandidate") -> bool:
        """Returns True if a given candidate passes, False otherwise."""

    @abstractmethod
    def reset(self) -> None:
        """Resets the state."""
