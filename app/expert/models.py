from django.db import models

from app.algorithm.models import Result, ResultBatch
from app.core.models.choices import (
    ExpertReviewStatus,
    QuestionnaireExpertReviewStatus,
)
from app.core.models.user import User
from app.expert.tasks import sendgrid_send_expert_review_completed_card


class ExpertBatchReview(models.Model):
    result_batch = models.OneToOneField(ResultBatch, on_delete=models.CASCADE)
    expert = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"groups__name": "Expert"},
    )
    review_completed = models.BooleanField(default=False)
    date_started = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.expert:
            return f"{self.expert.email} - {self.result_batch}"
        return f"{self.result_batch}"

    reviews: models.Manager["ResultReview"]

    def save(self, *args, **kwargs):
        if self.review_completed:
            self.result_batch.expert_review_required = ExpertReviewStatus.DONE.value
        else:
            self.result_batch.expert_review_required = ExpertReviewStatus.PENDING.value
        self.result_batch.save()
        super().save(*args, **kwargs)
        if (
            self.result_batch.questionnaire.common_expert_review_status
            == QuestionnaireExpertReviewStatus.COMPLETED.value
        ):
            sendgrid_send_expert_review_completed_card.delay(
                self.result_batch.questionnaire_id,
            )


class ResultReview(models.Model):
    result = models.OneToOneField(
        Result, on_delete=models.CASCADE, related_name="expert_review"
    )
    expert_batch_review = models.ForeignKey(
        ExpertBatchReview, on_delete=models.CASCADE, related_name="reviews"
    )
    expert_feedback = models.TextField(blank=True)
    expert_like = models.BooleanField(default=False)

    def __str__(self) -> str:
        if self.expert_batch_review.expert:
            return f"{self.expert_batch_review.expert.email}"
        return ""


class ExpertPlusReview(models.Model):
    expert_batch_review = models.ForeignKey(
        ExpertBatchReview, on_delete=models.CASCADE, related_name="expert_plus_reviews"
    )
    suggested_name = models.CharField(max_length=50, blank=True)
    name_rationale = models.TextField(blank=True)

    expert_feedback = models.TextField(blank=True)

    def __str__(self) -> str:
        if self.expert_batch_review.expert:
            return f"{self.expert_batch_review.expert.email}"
        return ""
