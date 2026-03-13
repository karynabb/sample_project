import pytest
from django.urls import reverse

from app.core.models import Payment
from app.core.models.price import ProductPrice
from tests.constants import CHECKOUT_URL


@pytest.fixture()
def fake_expert_review():
    fake_expert_review = ProductPrice.objects.create(
        name="Expert Review 49", stripe_price_id="stripe_id"
    )
    yield fake_expert_review
    fake_expert_review.delete()


@pytest.fixture()
def fake_expert_plus_review():
    fake_expert_plus_review = ProductPrice.objects.create(
        name="Expert Plus 40", stripe_price_id="stripe_id"
    )
    yield fake_expert_plus_review
    fake_expert_plus_review.delete()


@pytest.mark.django_db
def test_normal_view(
    fake_questionnaire, fake_expert_review, fake_expert_plus_review, api_client, mocker
):
    url = reverse("expert_buy")
    payload = {"questionnaire": fake_questionnaire.id, "is_expert_plus": False}
    session_data = {
        "id": "some_payment_id",
        "url": CHECKOUT_URL,
    }, "expert_in_the_loop"

    Payment.objects.create(
        status="completed",
        questionnaire=fake_questionnaire,
        user=fake_questionnaire.user,
        payment_type="initial",
        checkout_url=CHECKOUT_URL,
    )

    mocker.patch(
        "app.core.clients.stripe_client.client.StripeClient.create_expert_session",
        return_value=session_data,
    )
    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    assert response.json()["questionnaire"] == fake_questionnaire.id
    assert response.json()["stripe_id"] == "some_payment_id"
    assert response.json()["checkout_url"] == CHECKOUT_URL


@pytest.mark.django_db
def test_no_initial_payment_questionnaire(
    fake_questionnaire, fake_expert_review, api_client
):
    url = reverse("expert_buy")
    payload = {"questionnaire": fake_questionnaire.id, "is_expert_plus": False}

    response = api_client.post(url, data=payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_payment_already_exists(
    fake_questionnaire,
    fake_expert_review,
    fake_expert_plus_review,
    api_client,
):
    url = reverse("expert_buy")
    payload = {
        "questionnaire": fake_questionnaire.id,
        "is_expert_plus": False,
    }

    Payment.objects.create(
        status="completed",
        questionnaire=fake_questionnaire,
        user=fake_questionnaire.user,
        payment_type="initial",
        checkout_url=CHECKOUT_URL,
    )

    Payment.objects.create(
        status="completed",
        questionnaire=fake_questionnaire,
        user=fake_questionnaire.user,
        payment_type="expert_in_the_loop",
        checkout_url=CHECKOUT_URL,
    )

    response = api_client.post(url, data=payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_no_payload(api_client):
    url = reverse("expert_buy")
    response = api_client.post(url, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_wrong_user(api_client, fake_questionnaire, wrong_authed_user):
    url = reverse("expert_buy")
    payload = {"questionnaire": fake_questionnaire.id, "is_expert_plus": False}
    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == 403
