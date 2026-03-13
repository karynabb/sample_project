import uuid

import pytest

from app.core.models import Config, FeatureConfig


@pytest.fixture(autouse=True)
def default_feature_config(fake_pricing_plan, request):
    if "no_default_config" in request.keywords:
        yield
    else:
        feature_config = FeatureConfig.objects.create(
            active=True,
            version=str(uuid.uuid4())[:10],
            values=Config(pricing_plan=fake_pricing_plan.name.value, batch_size=24),
        )
        yield feature_config
        feature_config.delete()
