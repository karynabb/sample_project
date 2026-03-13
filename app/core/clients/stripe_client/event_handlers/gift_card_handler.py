import json

import stripe

from app.core.tasks import (
    create_hubspot_contact_for_gift_card,
    create_hubspot_deal,
    create_stripe_promo_codes,
)

from ..enums import ProductType
from .event_handler import EventHandler


class GiftCardHandler(EventHandler):
    _product_type = ProductType.GIFT_CARD

    def __init__(self):
        self._customer: stripe.Customer | None = None

    def handle_data(self, data: dict, status: str):
        if status != "completed":
            return
        email = self._get_email(data["object"])
        create_hubspot_contact_for_gift_card.delay(email)

        coupon_ids = json.loads(data["object"]["metadata"]["coupon_ids"])
        create_stripe_promo_codes.delay(
            email, self._get_name(data), coupon_ids=coupon_ids
        )
        amount_total = data["object"].get("amount_total")
        product_type = data["object"]["metadata"].get("product_type")
        create_hubspot_deal.delay(email, product_type, amount_total)
