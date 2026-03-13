import logging
from random import shuffle
from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction

from app.algorithm.candidate_validators import CandidateValidator, UniqueNameValidator
from app.algorithm.exceptions import BatchingException
from app.algorithm.managers import ResultManager
from app.core.models import FeatureConfig, Questionnaire
from app.core.models.choices import ExpertReviewStatus, ResultsGameComplexityLevel

logger = logging.getLogger(__name__)


class Pathway(models.Model):
    code = models.CharField(max_length=20, unique=True)
    global_rationale = models.TextField()
    active = models.BooleanField(default=True)
    candidates_per_batch = models.IntegerField(default=0)
    cascade_level = models.IntegerField(default=0)
    candidates: models.Manager["NameCandidate"]
    results: models.Manager["Result"]

    def __str__(self):
        return self.code


class NameCandidate(models.Model):
    name = models.CharField(max_length=50)
    rationale = models.TextField(blank=True)
    pathway = models.ForeignKey(
        Pathway, on_delete=models.CASCADE, related_name="candidates"
    )
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="candidates"
    )
    scoring = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("name", "questionnaire")

    def clean(self):
        from app.algorithm.utils import validate_new_name_candidate

        validate_new_name_candidate(self.questionnaire, self.name)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.full_clean()
        return super().save(*args, **kwargs)


class ResultBatch(models.Model):
    bought = models.BooleanField(default=False)
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="result_batches"
    )
    visible = models.BooleanField(default=False)
    bought_timestamp = models.DateTimeField(
        null=True,
        blank=True,
    )
    expert_review_required = models.CharField(
        max_length=10,
        choices=ExpertReviewStatus.choices,
        default=ExpertReviewStatus.NEW.value,
    )

    results: models.Manager["Result"]

    candidate_validators: list[CandidateValidator]

    def __init__(
        self,
        *args: Any,
        candidate_validators: list[CandidateValidator] | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        if candidate_validators is None:
            self.candidate_validators = [UniqueNameValidator()]
        else:
            self.candidate_validators = candidate_validators

    def add_result(self, name: str, rationale: str, pathway: Pathway):
        if self.results.count() >= FeatureConfig.get_active_config().batch_size:
            return False, None
        new_result = Result.objects.create(
            name=name, rationale=rationale, batch=self, pathway=pathway
        )
        return True, new_result

    def make_from_candidates(self):
        from app.algorithm.utils import candidates_from_pathway

        selected_candidates_ids = []
        for pathway in Pathway.objects.all():
            selected_candidates_ids.extend(
                candidates_from_pathway(pathway, self.questionnaire)
            )

        if len(selected_candidates_ids) < FeatureConfig.get_active_config().batch_size:
            raise BatchingException("Not enough candidates to create batch")

        shuffle(selected_candidates_ids)

        self.fill_from_candidates(candidate_ids=selected_candidates_ids)

    def fill_from_candidates(self, candidate_ids: list[int]) -> None:
        """
        Fill ResultBatch so that names do not contain identical or related words.
        """
        candidates = NameCandidate.objects.filter(id__in=candidate_ids)
        list_candidates = list(candidates)
        shuffle(list_candidates)

        candidates_batch = self._construct_candidates_batch(list_candidates)

        if len(candidates_batch) < FeatureConfig.get_active_config().batch_size:
            raise BatchingException("Not enough valid candidates to create a batch")

        results_batch = self._construct_results_batch(candidates_batch)
        with transaction.atomic():
            Result.objects.bulk_create(results_batch)
            NameCandidate.objects.filter(
                id__in=[c.id for c in candidates_batch]
            ).delete()

    def _construct_candidates_batch(
        self, candidates: list[NameCandidate]
    ) -> list[NameCandidate]:
        candidates_batch: list[NameCandidate] = []

        for candidate in candidates:
            if len(candidates_batch) == FeatureConfig.get_active_config().batch_size:
                break
            if not self._is_valid_candidate(candidate):
                continue
            candidates_batch.append(candidate)

        self._reset_validators()

        return candidates_batch

    def _is_valid_candidate(self, candidate: NameCandidate) -> bool:
        return all(
            validator.validate(candidate) for validator in self.candidate_validators
        )

    def _reset_validators(self) -> None:
        for validator in self.candidate_validators:
            validator.reset()

    def _construct_results_batch(
        self, candidates: list[NameCandidate]
    ) -> list["Result"]:
        return [
            Result(
                name=candidate.name,
                rationale="",
                batch=self,
                pathway=candidate.pathway,
            )
            for candidate in candidates
        ]


class Result(models.Model):
    objects = ResultManager()

    name = models.CharField(max_length=50)
    pathway = models.ForeignKey(
        Pathway, on_delete=models.CASCADE, related_name="results"
    )
    rationale = models.TextField(null=True, blank=True)
    batch = models.ForeignKey(
        ResultBatch, on_delete=models.CASCADE, related_name="results"
    )
    feedback = models.IntegerField(default=0)
    erroneous = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    game_complexity_level = models.IntegerField(
        choices=ResultsGameComplexityLevel.choices,
        default=ResultsGameComplexityLevel.UNAVAILABLE.value,
    )
    was_used_in_game = models.BooleanField(default=False)
    was_used_in_game_date = models.DateField(null=True, blank=True)
    number_was_used_in_game = models.IntegerField(default=0)
    example_phrases = ArrayField(
        models.CharField(max_length=100), null=True, blank=True
    )

    def __str__(self) -> str:
        return self.name

    @property
    def offering_description(self) -> str | None:
        if self.batch and self.batch.questionnaire:
            return self.batch.questionnaire.offering_description
        return None

    def revert_game_usage(self):
        from app.game.models import Game

        previous_game = Game.objects.get_latest_game_by_option_id(self.id)
        self.was_used_in_game_date = previous_game.date if previous_game else None
        if self.number_was_used_in_game > 0:
            self.number_was_used_in_game -= 1
        self.save()


class NegativeDataset(models.Model):
    word = models.CharField(max_length=30, unique=True)


class LMMCache(models.Model):
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="+"
    )
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE, related_name="+")
    cache = models.JSONField()
