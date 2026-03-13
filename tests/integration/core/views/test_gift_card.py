import pytest
from django.urls import reverse

from tests.constants import CHECKOUT_URL


@pytest.fixture(scope="function")
def fake_stripe_session():
    return {"customer_email": None, "customer_details": {"email": "test@example.com"}}


@pytest.mark.django_db
def test_get_gift_card_session(api_client, mocker):
    url = reverse("gift_cards_buy")
    payload = {"redirect_url": "http://testserver", "batches_amount": "1"}
    session_data = {
        "id": "some_payment_id",
        "url": CHECKOUT_URL,
    }

    mocker.patch(
        "app.core.clients.stripe_client.client.StripeClient.create_gift_card_session",
        return_value=session_data,
    )
    response = api_client.get(url, payload, format="json")

    assert response.status_code == 200
    assert response.json()["stripe_id"] == session_data["id"]
    assert response.json()["checkout_url"] == session_data["url"]


@pytest.mark.django_db
def test_get_gift_card_session_invalid_payload(api_client):
    url = reverse("gift_cards_buy")
    payload = {
        "redirect_url": "http://testserver",
        "batches_amount": "incorrect_batch_amount",
    }

    response = api_client.get(url, payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_no_payload(api_client):
    url = reverse("gift_cards_buy")
    response = api_client.get(url, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_get_email_with_promo_codes(api_client, mocker, fake_stripe_session):
    url = reverse("gift_cards_email")
    payload = {"stripe_id": "some_payment_id"}

    mocker.patch(
        "app.core.clients.stripe_client.client.StripeClient.retrieve_session",
        return_value=fake_stripe_session,
    )
    response = api_client.get(url, payload, format="json")

    assert response.status_code == 200
    assert (
        response.json()["email_with_promo_codes"]
        == fake_stripe_session["customer_details"]["email"]
    )


@pytest.mark.django_db
def test_get_email_with_no_id(api_client):
    url = reverse("gift_cards_email")
    response = api_client.get(url, format="json")

    assert response.status_code == 400
    assert response.json()["message"] == "Failed to retrieve the Stripe session."


@pytest.mark.django_db
def test_get_email_incorrect_id(api_client, mocker):
    url = reverse("gift_cards_email")
    payload = {"stripe_id": "incorrect_id"}

    mocker.patch(
        "app.core.clients.stripe_client.client.StripeClient.retrieve_session",
        return_value=None,
    )
    response = api_client.get(url, data=payload, format="json")

    assert response.status_code == 400
    assert response.json()["message"] == "Failed to retrieve the Stripe session."
