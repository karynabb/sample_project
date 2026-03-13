import pytest
from rest_framework.test import APIClient

from app.core.models import User


@pytest.fixture
def api_client(fake_user):
    api = APIClient()
    api.force_authenticate(fake_user)
    yield api


@pytest.fixture
def wrong_authed_user(api_client):
    """
    Fake objects in other fixtures are created linked to the
    tests.integration.fixtures.models.fake_user
    """
    wrong_user = User.objects.create(username="wrong")
    api_client.force_authenticate(wrong_user)
    yield wrong_user
    wrong_user.delete()
