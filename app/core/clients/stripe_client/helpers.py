import uuid

from django.shortcuts import get_object_or_404

from app.core.models import BatchPrice, Questionnaire


def get_batch_price_id(questionnaire_id: int) -> str:
    """
    Get stripe price for the requested batch based on the number of bought batches.
    If no batches were bought yet, it takes the price created by default.
    """
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    batches_number = questionnaire.get_bought_batches_number()
    price = BatchPrice.get_by_batch_number(batches_number)

    return price.stripe_price_id


def generate_promo_code() -> str:
    uuid4 = str(uuid.uuid4())
    stripe_compliant = uuid4.replace("-", "")
    return stripe_compliant[:16]
