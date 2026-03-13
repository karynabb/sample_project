from datetime import date
from typing import TYPE_CHECKING

from django.db import models
from django.shortcuts import get_object_or_404
from model_utils.models import TimeStampedModel
from pydantic import ValidationError

from app.core.models.choices import (
    ExpertReviewStatus,
    PaymentStatus,
    PaymentType,
    QuestionnaireExpertReviewStatus,
)
from app.core.typing import AnswerSchema

if TYPE_CHECKING:
    from app.algorithm.models import NameCandidate, ResultBatch

    from .payment import Payment


def default_questionnaire_name():
    return str(date.today())


class Questionnaire(TimeStampedModel):
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="questionnaires"
    )
    name = models.CharField(max_length=50, default=default_questionnaire_name)
    answers = models.JSONField()
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    failed = models.BooleanField(default=False)
    expert_review_payed = models.BooleanField(default=False)
    cascade_level_run = models.IntegerField(default=0)
    expert_plus_payed = models.BooleanField(default=False)
    picks_shown = models.BooleanField(default=False)
    offering_description = models.TextField(blank=True, null=True)

    payments: models.Manager["Payment"]
    candidates: models.Manager["NameCandidate"]
    result_batches: models.Manager["ResultBatch"]

    @property
    def is_payed(self) -> bool:
        return self.payments.filter(status=PaymentStatus.COMPLETED).exists()

    def __str__(self):
        return self.name

    @property
    def common_expert_review_status(self) -> QuestionnaireExpertReviewStatus:
        if self.expert_review_payed:
            bought_batches_count = self.result_batches.filter(bought=True).count()
            if (
                bought_batches_count
                == self.result_batches.filter(
                    expert_review_required=ExpertReviewStatus.DONE.value
                ).count()
            ):
                return QuestionnaireExpertReviewStatus.COMPLETED
            elif (
                bought_batches_count
                == self.result_batches.filter(
                    expert_review_required=ExpertReviewStatus.REQUIRED.value
                ).count()
            ):
                return QuestionnaireExpertReviewStatus.REQUESTED
            else:
                return QuestionnaireExpertReviewStatus.PENDING
        else:
            return QuestionnaireExpertReviewStatus.NOT_PAYED

    @property
    def amount_of_children(self):
        questionnaire_children = Questionnaire.objects.filter(parent=self)
        draft_children = DraftQuestionnaire.objects.filter(parent=self)
        return questionnaire_children.count() + draft_children.count()

    @property
    def algorithm_representation(self) -> dict:
        from app.algorithm.utils import questionnaire_data_to_algorithm_representation

        return questionnaire_data_to_algorithm_representation(self.answers)

    @property
    def has_available_batches(self) -> bool:
        return self.result_batches.filter(bought=False).exists()

    @property
    def has_completed_payment(self) -> bool:
        return self.payments.filter(
            payment_type=PaymentType.INITIAL, status=PaymentStatus.COMPLETED
        ).exists()

    @property
    def has_completed_expert_review_payment(self) -> bool:
        return self.payments.filter(
            payment_type=PaymentType.EXPERT_IN_THE_LOOP, status=PaymentStatus.COMPLETED
        ).exists()

    @property
    def has_completed_expert_plus_payment(self) -> bool:
        return self.payments.filter(
            payment_type=PaymentType.EXPERT_PLUS, status=PaymentStatus.COMPLETED
        ).exists()

    @property
    def has_completed_experts_payment(self) -> bool:
        return self.payments.filter(
            payment_type=PaymentType.EXPERTS, status=PaymentStatus.COMPLETED
        ).exists()

    @property
    def initial_payment_in_progress(self) -> "Payment | None":
        return (
            self.payments.filter(payment_type=PaymentType.INITIAL)
            .exclude(status=PaymentStatus.FAILED)
            .first()
        )

    def create_child(self, last_edited=0):
        """
        Creates a child from questionnaire
        If this object already has a parent, we link the new child to that parent
        """
        parent = self if not self.parent else self.parent
        child = DraftQuestionnaire.objects.create(
            user=self.user,
            name=f"{self.name} - {parent.amount_of_children + 1}",
            parent=parent,
            answers=self.answers,
            last_edited_question=last_edited,
        )
        return child

    def add_result(self, name: str, rationale: str, pathway):
        """Adds a result to the questionnaire, creating a new batch is necessary"""
        from app.algorithm.models import ResultBatch

        batches = ResultBatch.objects.filter(questionnaire=self)
        if batches:
            last_batch = batches.last()
            result, _ = last_batch.add_result(name, rationale, pathway)  # type: ignore
            if result:  # adding successful
                return
        # if all the batches are full or there aren't any batches -> create new
        batch = ResultBatch.objects.create(questionnaire=self)
        batch.add_result(name, rationale, pathway)

    def get_bought_batches_number(self) -> int:
        """Get number of bought batches."""
        if self.parent:
            questionnaire_parent = get_object_or_404(Questionnaire, id=self.parent_id)
            batches_number = questionnaire_parent.payments.filter(
                status=PaymentStatus.COMPLETED
            ).count()

            other_parent_questionnaire_childrens = Questionnaire.objects.filter(
                parent=questionnaire_parent
            ).exclude(id=self.id)
            batches_number += sum(
                [
                    other_parent_questionnaire_children.payments.filter(
                        status=PaymentStatus.COMPLETED
                    ).count()
                    for other_parent_questionnaire_children in other_parent_questionnaire_childrens
                ]
            )
        else:
            questionnaire_childrens = Questionnaire.objects.filter(parent=self)
            batches_number = sum(
                [
                    questionnaire_children.payments.filter(
                        status=PaymentStatus.COMPLETED
                    ).count()
                    for questionnaire_children in questionnaire_childrens
                ]
            )

        batches_number += self.payments.filter(status=PaymentStatus.COMPLETED).count()

        return batches_number

    def get_root_questionnaire(self):
        if self.parent is None:
            return self
        else:
            return self.parent.get_root_questionnaire()

    @property
    def siblings(self):
        if not self.parent:
            return Questionnaire.objects.none()
        return Questionnaire.objects.filter(parent=self.parent).exclude(pk=self.pk)

    def set_offering_description(self, offering_description: str):
        self.offering_description = offering_description
        self.save()


class DraftQuestionnaire(TimeStampedModel):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="drafts")
    name = models.CharField(max_length=50, default=default_questionnaire_name)
    answers = models.JSONField()
    parent = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    last_edited_question = models.IntegerField(null=True, blank=True)

    @property
    def ready_to_complete(self) -> bool:
        try:
            # The most reliable thing is to actually try and instantiate
            # the pydantic model because it will not only check the presense
            # of the keys but also handle optional fields under the hood and
            # still pass if they are not present
            AnswerSchema.parse_obj(self.answers)
            return True
        except ValidationError:
            return False
