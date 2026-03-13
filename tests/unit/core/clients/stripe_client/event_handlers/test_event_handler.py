import pytest

from app.core.clients.stripe_client.enums import ProductType
from app.core.clients.stripe_client.event_handlers import (
    BatchHandler,
    EventHandler,
    GiftCardHandler,
)
from tests.utils import create_stripe_event


@pytest.mark.parametrize(
    "product_type",
    [
        *[member.value for member in ProductType],
        *[member for member in ProductType],
    ],
)
def test_from_product_type__valid_product_type(product_type: ProductType | str):
    if isinstance(product_type, str):
        product_type_member = ProductType(product_type)
    else:
        product_type_member = product_type
    assert (
        EventHandler.from_product_type(product_type)._product_type
        == product_type_member
    )


def test_from_product_type__invalid_product_type():
    with pytest.raises(ValueError):
        EventHandler.from_product_type("unknown product type")


@pytest.mark.parametrize(
    "event_type,expected_status",
    [
        ("checkout.session.completed", "completed"),
        ("checkout.session.async_payment_succeeded", "completed"),
        ("checkout.session.async_payment_failed", "failed"),
        ("checkout.session.expired", "failed"),
    ],
)
def test_get_status(event_type, expected_status):
    event = create_stripe_event(event_type=event_type)
    assert EventHandler.get_status(event) == expected_status


def test_get_status__unknown_event():
    with pytest.raises(ValueError):
        EventHandler.get_status(create_stripe_event(event_type="abcdef"))


@pytest.mark.parametrize(
    "event_type,product_type",
    [("abc", "batch"), ("checkout.session.completed", "def"), ("abc", "def")],
)
def test_handle_event__not_implemented(event_type, product_type):
    event = create_stripe_event(event_type=event_type, product_type=product_type)

    response = EventHandler.handle_event(event)
    assert response.status_code == 501


@pytest.mark.parametrize(
    "event_type,product_type,expected_status,expected_handler",
    [
        ("checkout.session.completed", "batch", "completed", BatchHandler),
        (
            "checkout.session.async_payment_succeeded",
            "gift_card",
            "completed",
            GiftCardHandler,
        ),
        ("checkout.session.async_payment_failed", "batch", "failed", BatchHandler),
        ("checkout.session.expired", "gift_card", "failed", GiftCardHandler),
    ],
)
def test_handle_event__valid(
    mocker, event_type, product_type, expected_status, expected_handler
):
    event = create_stripe_event(event_type=event_type, product_type=product_type)

    handle_data_mock = mocker.patch.object(expected_handler, "handle_data")

    response = EventHandler.handle_event(event)
    assert response.status_code == 200
    handle_data_mock.assert_called_once_with(event["data"], expected_status)
