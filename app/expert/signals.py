from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from app.algorithm.models import NameCandidate
from app.core.models.choices import ExpertReviewStatus
from app.expert.models import ExpertBatchReview, ExpertPlusReview


@receiver(pre_delete, sender=ExpertBatchReview)
def set_required_status_on_delete(sender, instance, **kwargs):
    result_batch = instance.result_batch

    if result_batch:
        result_batch.expert_review_required = ExpertReviewStatus.REQUIRED.value
        result_batch.save()


@receiver(post_save, sender=ExpertPlusReview)
def delete_name_candidates_selected_in_expert_plus(sender, instance, **kwargs):
    if instance.suggested_name and instance.expert_batch_review.review_completed:
        NameCandidate.objects.filter(
            questionnaire=instance.expert_batch_review.result_batch.questionnaire,
            name=instance.suggested_name,
        ).delete()
