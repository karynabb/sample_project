import pytest

from app.core.models import BatchPrice, PricingPlan, PricingPlanName


@pytest.fixture(autouse=True)
def prepare_prices(fake_pricing_plan):
    prices = BatchPrice.objects.bulk_create(
        [
            BatchPrice(
                stripe_price_id=f"A_test_{i}",
                batch_number=i,
                pricing_plan=fake_pricing_plan,
            )
            for i in range(5)
        ]
    )
    yield
    for price in prices:
        price.delete()


@pytest.mark.django_db
def test_get_active_batch_prices(fake_pricing_plan):
    plan_b, _ = PricingPlan.objects.get_or_create(name=PricingPlanName.B)

    BatchPrice.objects.bulk_create(
        [
            BatchPrice(
                stripe_price_id=f"B_test_{i}",
                batch_number=i,
                pricing_plan=plan_b,
            )
            for i in range(5)
        ]
    )

    active_prices = BatchPrice.get_active_batch_prices()
    assert len(list(active_prices.all())) == 5
    for price in active_prices:
        assert price.pricing_plan.pk == fake_pricing_plan.pk
        assert price.stripe_price_id.startswith("A_")


@pytest.mark.django_db
def test_get_by_batch_number():
    batch_price = BatchPrice.get_by_batch_number(2)
    assert batch_price.batch_number == 2
    assert batch_price.stripe_price_id == "A_test_2"


@pytest.mark.django_db
def test_get_by_batch_number__overflow():
    batch_price = BatchPrice.get_by_batch_number(10)
    assert batch_price.batch_number == 4
    assert batch_price.stripe_price_id == "A_test_4"
