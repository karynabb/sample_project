import operator
from typing import ClassVar

from cachetools import TTLCache, cachedmethod
from django.db import models, transaction
from pydantic import BaseModel

from app.core.pydantic_serialization import PydanticDecoder, PydanticEncoder

from .choices import PricingPlanName


class Config(BaseModel):
    pricing_plan: PricingPlanName
    batch_size: int


class ConfigDecoder(PydanticDecoder):
    model = Config


class FeatureConfig(models.Model):
    """
    This model acts as a config storage for feature flag deployments.

    It's purpose is to decouple deployment from release and be able
    to adjust and rollback the control flow without the new deployment.
    """

    active = models.BooleanField()
    version = models.CharField(max_length=15, unique=True)
    values: Config = models.JSONField(  # type: ignore[assignment]
        encoder=PydanticEncoder, decoder=ConfigDecoder
    )

    _active_config_cache: ClassVar[TTLCache] = TTLCache(maxsize=1, ttl=3600)

    @classmethod
    @cachedmethod(operator.attrgetter("_active_config_cache"))
    def get_active_config(cls) -> Config:
        feature_config = FeatureConfig.objects.filter(active=True).first()
        if feature_config is None:
            raise Exception("Active feature config not found.")
        return feature_config.values

    def save(self, *args, **kwargs):
        """
        Inactivates the current feature config upon saving a new active one.
        """
        if not self.active:
            return super().save(*args, **kwargs)
        with transaction.atomic():
            # This must happen inside of a transaction to make sure
            # that we won't have zero active configs
            FeatureConfig.objects.filter(active=True).update(active=False)
            super().save(*args, **kwargs)
        # Reset the cache to ensure that the newly active config is loaded next time
        self._active_config_cache.clear()
