import pytest

from tests.constants import CHECKOUT_URL


@pytest.fixture(autouse=True)
def create_session_mock(mocker):
    mock = mocker.patch(
        "app.core.clients.stripe_client.client.StripeClient.create_checkout_session"
    )
    mock.return_value = {
        "id": "some_payment_id",
        "url": CHECKOUT_URL,
    }
    yield mock
