import pytest
from django.db.models import QuerySet

from app.core.models import Config, FeatureConfig, PricingPlanName


@pytest.fixture(autouse=True)
def reset_configs():
    FeatureConfig._active_config_cache.clear()
    yield
    FeatureConfig.objects.all().delete()
    FeatureConfig._active_config_cache.clear()


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_get_active_config__no_configs_raises():
    with pytest.raises(Exception):
        FeatureConfig.get_active_config()


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_get_active_config__no_active_config_raises():
    FeatureConfig.objects.create(
        active=False,
        version="test",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )
    with pytest.raises(Exception):
        FeatureConfig.get_active_config()


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_get_active_config__correct_config():
    active_config = FeatureConfig(
        active=True,
        version="active",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )
    other_config = FeatureConfig(
        active=False,
        version="other",
        values=Config(pricing_plan=PricingPlanName.B.value, batch_size=12),
    )
    FeatureConfig.objects.bulk_create([active_config, other_config])

    loaded_config = FeatureConfig.get_active_config()

    assert loaded_config.dict() == active_config.values.dict()


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_get_active_config__uses_cache(mocker):
    FeatureConfig.objects.create(
        active=True,
        version="active",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )

    first_mock = mocker.patch.object(QuerySet, "first")

    FeatureConfig.get_active_config()
    FeatureConfig.get_active_config()

    first_mock.assert_called_once()


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_save__does_nothing_for_inactive():
    active_config = FeatureConfig.objects.create(
        active=True,
        version="active",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )

    FeatureConfig.objects.create(
        active=False,
        version="other",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )

    active_config.refresh_from_db()
    assert active_config.active


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_save__makes_previous_inactive():
    first_active_config = FeatureConfig.objects.create(
        active=True,
        version="active",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )

    FeatureConfig.objects.create(
        active=True,
        version="new_act",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )

    first_active_config.refresh_from_db()
    assert not first_active_config.active


@pytest.mark.django_db
@pytest.mark.no_default_config
def test_save__clears_cache():
    old_config = FeatureConfig.objects.create(
        active=True,
        version="1.0.0",
        values=Config(pricing_plan=PricingPlanName.A.value, batch_size=24),
    )
    active_config = FeatureConfig.get_active_config()
    assert old_config.values.dict() == active_config.dict()

    new_config = FeatureConfig.objects.create(
        active=True,
        version="1.0.1",
        values=Config(pricing_plan=PricingPlanName.B.value, batch_size=12),
    )
    active_config = FeatureConfig.get_active_config()
    assert new_config.values.dict() == active_config.dict()
