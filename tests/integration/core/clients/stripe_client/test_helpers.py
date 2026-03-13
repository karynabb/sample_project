import pytest

from app.core.clients.stripe_client.helpers import get_batch_price_id
from app.core.models import BatchPrice, Payment


@pytest.fixture
def batch_prices(fake_pricing_plan):
    batch_prices = [
        BatchPrice(
            pricing_plan=fake_pricing_plan,
            batch_number=i,
            stripe_price_id=f"price_{i}",
            stripe_coupon_id=f"coupon_{i}",
        )
        for i in range(4)
    ]
    BatchPrice.objects.bulk_create(batch_prices)
    yield batch_prices
    for price in batch_prices:
        price.delete()


@pytest.fixture
def completed_payments(fake_questionnaire, request):
    payments = [
        Payment(
            questionnaire=fake_questionnaire,
            user=fake_questionnaire.user,
            status="completed",
            stripe_id="test_id",
            checkout_url="test_url",
            payment_type="buy_more" if i else "initial",
        )
        for i in range(request.param)
    ]
    Payment.objects.bulk_create(payments)
    yield payments, request.param
    for payment in payments:
        payment.delete()


@pytest.mark.django_db
@pytest.mark.parametrize("completed_payments", [0, 1, 2, 3], indirect=True)
def test_get_batch_price_id(batch_prices, fake_questionnaire, completed_payments):
    _, payments_amount = completed_payments
    batch_price_id = get_batch_price_id(fake_questionnaire.id)
    assert batch_price_id == f"price_{payments_amount}"
