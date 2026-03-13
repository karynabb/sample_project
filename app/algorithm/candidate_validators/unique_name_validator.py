from typing import TYPE_CHECKING

from .base_validator import CandidateValidator

if TYPE_CHECKING:
    from app.algorithm.models import NameCandidate


class UniqueNameValidator(CandidateValidator):
    """
    Check that all the names in the batch satisfy the uniqueness rule:

    any word in any name should not be a part of any word in any other name.
    """

    def __init__(self) -> None:
        self._added_words: set[str] = set()

    def validate(self, candidate: "NameCandidate") -> bool:
        if self._is_valid_name(candidate_name=candidate.name):
            self._added_words.update(candidate.name.split())
            return True
        return False

    def reset(self) -> None:
        self._added_words = set()

    def _is_valid_name(self, candidate_name: str) -> bool:
        """
        Check if the name is valid and can be added to the result batch.

        Validity is determined by the name uniqueness.
        Every word in the name should follow these rules:
          - it should not contain any already added words;
          - it itself should not be a part of the any already added word.
        """
        words_to_check = candidate_name.split()
        for added_word in self._added_words:
            for word in words_to_check:
                if added_word in word:
                    return False
                if word in added_word:
                    return False
        return True
