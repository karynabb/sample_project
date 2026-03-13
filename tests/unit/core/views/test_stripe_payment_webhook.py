import json
from os.path import join
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from celery import Task
from django.db.models import QuerySet
from django.urls import reverse
from rest_framework.test import APIClient
from stripe import Webhook

from app.core.models import Payment


@pytest.fixture
def webhook_payload():
    json_path = join(Path(__file__).parent, "example_webhook_payload.json")
    with open(json_path) as payload_file:
        payload = json.load(payload_file)
    return payload


@pytest.fixture
def preparation_fixtures(
    request, fake_payment: Payment, webhook_payload: dict[str, Any], mocker
):
    """
    Returns a tuple with:
        - fake payment that will be used during the webhook processing;
        - webhook payload;
        - MagicMock that will be in place of celery.Task.delay.

    Also mocks .save() method to prevent DB calls.
    """
    event_type = request.param

    construct_event_mock = mocker.patch.object(Webhook, "construct_event")
    webhook_payload["type"] = event_type
    construct_event_mock.return_value = webhook_payload

    payment_get_mock = mocker.patch.object(QuerySet, "get")
    payment_get_mock.return_value = fake_payment

    mocker.patch.object(Payment, "save")

    delay_mock = mocker.patch.object(Task, "delay")

    yield fake_payment, webhook_payload, delay_mock


@pytest.mark.parametrize(
    "preparation_fixtures", ["something.unsupported"], indirect=True
)
def test_webhook__unsupported_event_type(
    preparation_fixtures: tuple[Payment, dict[str, Any], MagicMock],
):
    _, _, delay_mock = preparation_fixtures
    url = reverse("payments_webhook")

    # Don't need to supply data through endpoint
    # as it's verified and loaded using Webhook.construct_event
    response = APIClient().post(url, data={}, format="json")
    assert response.status_code == 501
    delay_mock.assert_not_called


@pytest.mark.parametrize(
    "preparation_fixtures",
    ["checkout.session.expired", "checkout.session.async_payment_failed"],
    indirect=True,
)
def test_webhook__payment_failed(
    preparation_fixtures: tuple[Payment, dict[str, Any], MagicMock],
):
    fake_payment, _, delay_mock = preparation_fixtures
    url = reverse("payments_webhook")

    response = APIClient().post(url, data={}, format="json")

    assert response.status_code == 200
    assert fake_payment.status == "failed"
    delay_mock.assert_not_called


@pytest.mark.parametrize(
    "preparation_fixtures",
    ["checkout.session.completed", "checkout.session.async_payment_succeeded"],
    indirect=True,
)
def test_webhook__session_completed(
    preparation_fixtures: tuple[Payment, dict[str, Any], MagicMock],
):
    fake_payment, webhook_payload, delay_mock = preparation_fixtures
    url = reverse("payments_webhook")

    response = APIClient().post(url, data={}, format="json")

    assert response.status_code == 200
    assert fake_payment.status == "completed"

    delay_mock.assert_called_once_with(
        fake_payment.user.email,
        fake_payment.payment_type,
        webhook_payload["data"]["object"]["amount_total"],
    )
