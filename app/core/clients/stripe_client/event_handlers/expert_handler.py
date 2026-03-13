import logging

from django.http import Http404
from django.urls import reverse

from app.algorithm.models import ResultBatch
from app.algorithm.tasks import generate_name_candidates
from app.core.models import Payment, Questionnaire, User
from app.expert import models
from app.expert.models import ExpertBatchReview
from app.expert.tasks import (
    sendgrid_send_expert_next_step_card,
    sendgrid_send_expert_review_required_card,
)

from ..enums import ProductType
from .event_handler import EventHandler

logger = logging.getLogger(__name__)


class ExpertHandler(EventHandler):
    _product_type = ProductType.EXPERT

    def handle_data(self, data: dict, status: str):
        checkout_id = data["object"]["id"]
        try:
            payment = Payment.objects.select_related("questionnaire").get(
                stripe_id=checkout_id
            )
        except Payment.DoesNotExist:
            message = f"Payment {checkout_id} does not exist"
            logger.error("Expert handler: " + message)
            raise Http404(message)
        payment.status = status
        payment.save()
        payment_type = payment.payment_type

        if status == "completed":
            from app.core.tasks import create_hubspot_deal

            root_questionnaire = payment.questionnaire
            modified_root_questionnaire_data = self.__set_expert_review_payed(
                root_questionnaire, payment_type
            )
            if payment_type == "expert_in_the_loop":
                recipients = self.get_expert_email_recipients()
                sendgrid_send_expert_review_required_card.delay(
                    recipients, [modified_root_questionnaire_data], is_expert_plus=False
                )
                logger.info(f"ExpertHandler: sent expert email to {recipients}")
            amount_total = data["object"].get("amount_total")
            create_hubspot_deal.delay(
                payment.user.email, payment.payment_type, amount_total
            )

    @staticmethod
    def get_expert_email_recipients():
        experts = User.objects.filter(groups__name="Expert")
        recipients = []

        for expert in experts:
            recipients.append((expert.email, expert.username))

        return recipients

    def __set_expert_review_payed(
        self, questionnaire: Questionnaire, payment_type: str
    ):
        if payment_type == "expert_plus":
            if questionnaire.common_expert_review_status == "completed":
                questionnaire.picks_shown = True
            questionnaire.expert_plus_payed = True
        elif payment_type == "experts":
            questionnaire.expert_plus_payed = True
        questionnaire.expert_review_payed = True
        questionnaire.save()
        self._send_expert_next_step_card(questionnaire.id, payment_type)
        return self._prepare_modified_data(payment_type, questionnaire)

    def _prepare_modified_data(self, payment_type: str, questionnaire: Questionnaire):
        modified_data = []
        for result_batch in ResultBatch.objects.filter(questionnaire=questionnaire):
            if result_batch.bought:
                result_batch.expert_review_required = "required"
                result_batch.save()

                if payment_type == "expert_in_the_loop" or payment_type == "experts":
                    review = self.create_empty_reviews_for_payed_batch(result_batch)
                    modified_data.append(self.format_review_msg(review))
                    if payment_type == "experts":
                        self.create_three_empty_expert_plus_reviews_for_payed_batch(
                            review
                        )
                elif payment_type == "expert_plus":
                    review = ExpertBatchReview.objects.get(result_batch=result_batch)
                    if review.review_completed:
                        review.review_completed = False
                        review.save()
                    modified_data.append(self.format_review_msg(review))
                    self.create_three_empty_expert_plus_reviews_for_payed_batch(review)

        if modified_data:
            modified_data.insert(0, self.format_questionnaire_msg(questionnaire))

        if payment_type == "experts" or payment_type == "expert_plus":
            generate_name_candidates.delay(questionnaire.id, False, True)

        return modified_data

    @staticmethod
    def _send_expert_next_step_card(questionnaire_id, payment_type):
        sendgrid_send_expert_next_step_card.delay(
            questionnaire_id, is_expert_plus_separately=payment_type == "expert_plus"
        )

    @staticmethod
    def format_questionnaire_msg(questionnaire: Questionnaire):
        questionnaire_admin_url = reverse(
            "admin:{}_{}_change".format(
                questionnaire._meta.app_label, questionnaire._meta.model_name
            ),
            args=[questionnaire.id],
        )
        return [
            {
                "title": "Questionnaire link: ",
                "url": questionnaire_admin_url,
                "display_id": f"{questionnaire.name}",
            }
        ]

    @staticmethod
    def format_review_msg(review: models.ExpertBatchReview):
        review_link = reverse(
            "admin:{}_{}_change".format(
                review._meta.app_label, review._meta.model_name
            ),
            args=[review.id],
        )
        return [
            {
                "title": "Review batch link: ",
                "url": review_link,
                "display_id": f"review-{review.id}",
            }
        ]

    def get_reviews_for_payed_batch(self, batch: ResultBatch):
        expert_batch_review = models.ExpertBatchReview.objects.filter(
            result_batch=batch
        ).first()
        return expert_batch_review

    @staticmethod
    def create_empty_reviews_for_payed_batch(batch: ResultBatch):
        expert_batch_review, _ = models.ExpertBatchReview.objects.get_or_create(
            result_batch=batch, defaults={"result_batch": batch}
        )
        models.ResultReview.objects.bulk_create(
            [
                models.ResultReview(
                    result=result, expert_batch_review=expert_batch_review
                )
                for result in batch.results.all()
            ]
        )
        return expert_batch_review

    @staticmethod
    def create_three_empty_expert_plus_reviews_for_payed_batch(
        batch_review: ExpertBatchReview,
    ):
        models.ExpertPlusReview.objects.bulk_create(
            [
                models.ExpertPlusReview(expert_batch_review=batch_review)
                for _ in range(3)
            ]
        )
        return batch_review
