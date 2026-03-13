import pytest
from django.urls import reverse

from tests.constants import CHECKOUT_URL


@pytest.fixture
def completed_payment(fake_payment):
    fake_payment.status = "completed"
    fake_payment.save()
    yield fake_payment


@pytest.mark.django_db
def test_normal_view(create_session_mock, fake_batch, api_client, completed_payment):
    url = reverse("payments_buy_more")
    payload = {"questionnaire": fake_batch.questionnaire.id}
    response = api_client.post(url, data=payload, format="json")

    create_session_mock.assert_called_once_with(
        "http://testserver/journey/", fake_batch.questionnaire.id
    )
    assert response.status_code == 201
    assert response.json()["questionnaire"] == fake_batch.questionnaire.id
    assert response.json()["stripe_id"] == "some_payment_id"
    assert response.json()["checkout_url"] == CHECKOUT_URL


@pytest.mark.django_db
def test_no_initial_payment(fake_questionnaire, api_client):
    url = reverse("payments_buy_more")
    payload = {"questionnaire": fake_questionnaire.id}
    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_no_batches(fake_questionnaire, api_client, fake_batch):
    fake_batch.bought = True
    fake_batch.save()
    url = reverse("payments_buy_more")
    payload = {"questionnaire": fake_questionnaire.id}
    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_wrong_user(api_client, fake_questionnaire, wrong_authed_user):
    url = reverse("payments_buy_more")
    payload = {"questionnaire": fake_questionnaire.id}
    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_no_payload(api_client):
    url = reverse("payments_buy_more")
    response = api_client.post(url, format="json")

    assert response.status_code == 404
