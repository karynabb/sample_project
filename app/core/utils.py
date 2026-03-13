import logging

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from app.algorithm.models import NegativeDataset, ResultBatch
from app.core import sendgrid
from app.core.models import FeatureConfig, PricingPlanName, Questionnaire
from app.core.models.choices import ExpertReviewStatus
from app.core.sendgrid import (
    failed_journey_external_email,
    failed_journey_internal_email,
)
from app.expert.tasks import sendgrid_send_expert_review_required_card

logger = logging.getLogger(__name__)


def get_rsa_keys_from_auth0() -> dict:
    """Get two RSA key pairs for each user pool for decode Auth0 Jwt Token."""
    try:
        response = requests.get(settings.AUTH0_JWKS_URL)
        return response.json()
    except requests.exceptions.RequestException:
        raise AuthenticationFailed("Can't get RSA key pair.")


def get_auth0_user_data(access_token: str) -> dict:
    """Try to get user data from auth0 using user access token."""
    try:
        response = requests.get(
            settings.AUTH0_USER_INFO, {"access_token": access_token}
        )
        return response.json()
    except requests.exceptions.RequestException:
        raise AuthenticationFailed("Can't get user data due to API error.")


def word_is_negative(word: str) -> bool:
    return NegativeDataset.objects.filter(word__iexact=word).exists()


def list_of_negative_words(words: list[str]) -> list[str]:
    """
    Returns the list of the same length, when the output is either empty string
    or the words itself
    """
    output_list = []
    for word in words:
        if word_is_negative(word):
            output_list.append(word)
        else:
            output_list.append("")
    return output_list


def check_negative_dataset(answers: dict[str, str | list]) -> dict[str, list[str]]:
    """
    Returns all the values that exist in the negative dataset
    """
    error_dict = {}
    for key, value in answers.items():
        if isinstance(value, str):
            if word_is_negative(value):
                error_dict[key] = [value]
        elif isinstance(value, list):
            if any(failed_words := list_of_negative_words(value)):
                error_dict[key] = failed_words
    return error_dict


def fail_journey(questionnaire: Questionnaire):
    questionnaire.failed = True
    failed_journey_external_email(questionnaire)
    failed_journey_internal_email(questionnaire)
    questionnaire.save()


def get_is_pricing_plan_free() -> bool:
    return FeatureConfig.get_active_config().pricing_plan == PricingPlanName.FREE


def get_first_batch(questionnaire: Questionnaire):
    from app.algorithm.tasks import generate_name_candidates

    generate_name_candidates.delay(questionnaire.id, True)
    try:
        sendgrid.next_step_email(questionnaire)
    except Exception as e:  # errors in mail dont interrupt saving
        logger.warning(e)


def get_new_batch(questionnaire: Questionnaire) -> dict | None:
    from app.algorithm.tasks import create_batch
    from app.core.clients.stripe_client.event_handlers import ExpertHandler

    total_number_of_completed = questionnaire.payments.filter(status="completed")
    total_batches_bought = ResultBatch.objects.filter(
        questionnaire=questionnaire, bought=True
    )
    if (
        total_batches_bought.count() < total_number_of_completed.count()
        or get_is_pricing_plan_free()
    ):
        first_unbought_batch = ResultBatch.objects.filter(
            questionnaire=questionnaire, bought=False
        ).first()
        if first_unbought_batch:
            first_unbought_batch.bought = True
            first_unbought_batch.bought_timestamp = timezone.now()
            create_batch.delay(questionnaire.id, [])
            if questionnaire.expert_review_payed:
                first_unbought_batch.expert_review_required = (
                    ExpertReviewStatus.REQUIRED.value
                )
            first_unbought_batch.save()
            if questionnaire.expert_review_payed:
                recipients = ExpertHandler.get_expert_email_recipients()
                review = ExpertHandler.create_empty_reviews_for_payed_batch(
                    first_unbought_batch
                )
                if questionnaire.expert_plus_payed:
                    ExpertHandler.create_three_empty_expert_plus_reviews_for_payed_batch(
                        review
                    )
                questionnaire = first_unbought_batch.questionnaire

                msg = [
                    ExpertHandler.format_questionnaire_msg(questionnaire),
                    ExpertHandler.format_review_msg(review),
                ]
                is_expert_plus = questionnaire.expert_plus_payed
                sendgrid_send_expert_review_required_card.delay(
                    recipients, msg, is_expert_plus
                )
            return {"new_batch_id": first_unbought_batch.id}
    return None
