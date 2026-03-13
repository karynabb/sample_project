from django.db import models

from .choices import PricingPlanName
from .feature_config import FeatureConfig


class PricingPlan(models.Model):
    name = models.CharField(
        choices=PricingPlanName.choices,
        max_length=5,
        default=PricingPlanName.A.value,
        unique=True,
    )

    batch_prices: models.Manager["BatchPrice"]


class ProductPrice(models.Model):
    name = models.CharField(max_length=50)
    stripe_price_id = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class BatchPrice(models.Model):
    stripe_price_id = models.CharField(max_length=50)
    stripe_coupon_id = models.CharField(max_length=20, null=True, blank=True)

    batch_number = models.IntegerField()

    pricing_plan = models.ForeignKey(
        PricingPlan,
        on_delete=models.CASCADE,
        related_name="batch_prices",
    )

    @classmethod
    def get_active_batch_prices(cls) -> models.QuerySet["BatchPrice"]:
        """Returns batch prices corresponding to the current active pricing plan."""
        active_pricing_plan_name = FeatureConfig.get_active_config().pricing_plan
        active_pricing_plan = PricingPlan.objects.prefetch_related("batch_prices").get(
            name=active_pricing_plan_name
        )
        return active_pricing_plan.batch_prices.order_by("batch_number")

    @classmethod
    def get_by_batch_number(cls, batch_number: int) -> "BatchPrice":
        active_prices = BatchPrice.get_active_batch_prices()
        batch_prices_count = active_prices.count()
        return active_prices.get(batch_number=min(batch_number, batch_prices_count - 1))

    @classmethod
    def get_first_n_prices(cls, batches_amount: int) -> list["BatchPrice"]:
        return list(
            BatchPrice.get_active_batch_prices().filter(batch_number__lt=batches_amount)
        )
