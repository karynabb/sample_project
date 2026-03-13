import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Type

import stripe
from django.http import HttpResponse

from app.core.clients.stripe_client.client import StripeClient
from app.core.clients.stripe_client.enums import ProductType

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    _product_type: ClassVar[ProductType]
    _product_type_to_handler: ClassVar[dict[ProductType, Type["EventHandler"]]] = {}

    def __init__(self):
        self._customer: stripe.Customer | None = None

    def __init_subclass__(cls) -> None:
        cls._product_type_to_handler[cls._product_type] = cls
        return super().__init_subclass__()

    @classmethod
    def from_product_type(cls, product_type: ProductType | str) -> "EventHandler":
        if isinstance(product_type, str):
            try:
                product_type = ProductType(product_type)
            except ValueError as e:
                logger.error(f"Unknown product type: {product_type}")
                raise e

        handler_cls = cls._product_type_to_handler.get(product_type, None)
        if handler_cls is None:
            logger.error(f"Product type {product_type} doesn't have an event handler")
            raise ValueError()
        return handler_cls()

    @classmethod
    def get_status(cls, event: stripe.Event) -> str:
        event_type_to_status = {
            "checkout.session.completed": "completed",
            "checkout.session.async_payment_succeeded": "completed",
            "checkout.session.async_payment_failed": "failed",
            "checkout.session.expired": "failed",
        }
        new_status = event_type_to_status.get(event["type"])
        if new_status is None:
            logger.error(f"Unsupported event type {event['type']}")
            raise ValueError()
        return new_status

    @classmethod
    def handle_event(cls, event: stripe.Event) -> HttpResponse:
        product_type = event["data"]["object"]["metadata"].get("product_type")
        try:
            handler = cls.from_product_type(product_type)
            status = cls.get_status(event)
        except ValueError:
            return HttpResponse(status=501)
        handler.handle_data(event["data"], status)
        return HttpResponse(status=200)

    def _get_email(self, data: dict) -> str:
        maybe_email = data.get("customer_email", None)
        if maybe_email is not None:
            return maybe_email
        maybe_email = data["customer_details"].get("email", None)
        if maybe_email is not None:
            return maybe_email
        if self._customer is None:
            self._customer = StripeClient.retrieve_customer(data.get("customer", ""))
        return self._customer["email"]

    def _get_name(self, data: dict) -> str:
        maybe_name = data["object"]["customer_details"].get("name", None)
        if maybe_name is not None:
            return maybe_name
        if self._customer is None:
            self._customer = StripeClient.retrieve_customer(data["object"]["customer"])
        return self._customer["name"]

    @abstractmethod
    def handle_data(self, data: dict, status: str):
        pass
