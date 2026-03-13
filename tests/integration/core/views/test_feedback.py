import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_endpoint(api_client, fake_result):
    url = reverse("feedback", kwargs={"id": fake_result.id})
    assert fake_result.feedback != 3
    api_client.patch(url, data={"feedback": 3}, format="json")
    fake_result.refresh_from_db()
    assert fake_result.feedback == 3


@pytest.mark.django_db
def test_wrong_user(api_client, fake_result, wrong_authed_user):
    url = reverse("feedback", kwargs={"id": fake_result.id})
    response = api_client.patch(url, data={"feedback": 3}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_erroneous(api_client, fake_result):
    url = reverse("feedback", kwargs={"id": fake_result.id})
    assert not fake_result.erroneous
    api_client.patch(url, data={"erroneous": True}, format="json")
    fake_result.refresh_from_db()
    assert fake_result.erroneous


@pytest.mark.django_db
def test_favorite(api_client, fake_result):
    url = reverse("feedback", kwargs={"id": fake_result.id})
    assert not fake_result.favorite
    api_client.patch(url, data={"favorite": True}, format="json")
    fake_result.refresh_from_db()
    assert fake_result.favorite
