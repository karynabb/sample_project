import pytest
from django.urls import reverse

from app.core.models import Payment
from tests.constants import CHECKOUT_URL


@pytest.mark.django_db
def test_normal_view(fake_questionnaire, create_session_mock, api_client):
    url = reverse("payments_create")
    payload = {"questionnaire": fake_questionnaire.id}
    response = api_client.post(url, data=payload, format="json")

    create_session_mock.assert_called_once_with(
        "http://testserver/questionnaire/", fake_questionnaire.id
    )
    assert response.status_code == 201
    assert response.json()["questionnaire"] == fake_questionnaire.id
    assert response.json()["stripe_id"] == "some_payment_id"
    assert response.json()["checkout_url"] == CHECKOUT_URL


@pytest.mark.django_db
def test_payment_already_exists(fake_questionnaire, api_client):
    Payment.objects.create(
        status="completed",
        questionnaire=fake_questionnaire,
        user=fake_questionnaire.user,
        payment_type="initial",
        checkout_url=CHECKOUT_URL,
    )

    url = reverse("payments_create")
    payload = {"questionnaire": fake_questionnaire.id}
    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_wrong_user(api_client, fake_questionnaire, wrong_authed_user):
    url = reverse("payments_create")
    payload = {"questionnaire": fake_questionnaire.id}
    response = api_client.post(url, data=payload, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_no_payload(api_client):
    url = reverse("payments_create")
    response = api_client.post(url, format="json")

    assert response.status_code == 404
