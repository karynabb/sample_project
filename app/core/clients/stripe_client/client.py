import json
import logging
from typing import Any
from urllib import parse

import stripe
from django.conf import settings

from app.core.models import BatchPrice

from ...enums import DonationSourceEnum
from .enums import ProductType
from .helpers import generate_promo_code, get_batch_price_id

stripe.api_key = settings.STRIPE_API_KEY

logger = logging.getLogger(__name__)


class StripeClient:
    @classmethod
    def create_checkout_session(
        cls, redirect_url: str, questionnaire_id: int
    ) -> stripe.checkout.Session:
        """Creates checkout session for payment."""
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": get_batch_price_id(questionnaire_id=questionnaire_id),
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{redirect_url}{questionnaire_id}?result=success",
            cancel_url=f"{redirect_url}{questionnaire_id}?result=cancelled",
            metadata={"product_type": ProductType.BATCH.value},
            allow_promotion_codes=True,
        )
        return session

    @classmethod
    def create_expert_session(
        cls,
        redirect_url: str,
        questionnaire_id: int,
        expert_review_price: str,
        expert_plus_price: str,
        is_expert_plus: bool,
        is_expert_in_the_loop_payed: bool,
    ):
        line_items = []
        payment_type = "experts"
        if is_expert_plus and not is_expert_in_the_loop_payed:
            line_items = [
                {
                    "price": expert_plus_price,
                    "quantity": 1,
                },
                {
                    "price": expert_review_price,
                    "quantity": 1,
                },
            ]
        elif is_expert_plus and is_expert_in_the_loop_payed:
            line_items = [
                {
                    "price": expert_plus_price,
                    "quantity": 1,
                }
            ]
            payment_type = "expert_plus"
        elif not is_expert_plus and not is_expert_in_the_loop_payed:
            line_items = [
                {
                    "price": expert_review_price,
                    "quantity": 1,
                }
            ]
            payment_type = "expert_in_the_loop"

        session = stripe.checkout.Session.create(
            line_items=line_items,
            mode="payment",
            success_url=f"{redirect_url}{questionnaire_id}?result=success",
            cancel_url=f"{redirect_url}{questionnaire_id}?result=cancelled",
            metadata={"product_type": ProductType.EXPERT.value},
            allow_promotion_codes=True,
        )
        return session, payment_type

    @classmethod
    def create_gift_card_session(
        cls, front_base_url: str, redirect_url: str, batches_amount: int
    ) -> stripe.checkout.Session:
        batch_price = BatchPrice.get_by_batch_number(batches_amount)

        success_params = parse.urlencode(
            {
                "result": "success",
                "redirect_url": redirect_url,
            }
        )
        cancelled_params = parse.urlencode(
            {
                "result": "cancelled",
                "redirect_url": redirect_url,
            }
        )
        session = stripe.checkout.Session.create(
            line_items=cls._get_gift_card_line_items([batch_price.stripe_price_id]),
            mode="payment",
            success_url=f"{front_base_url}gift-cards/buy?{success_params}",
            cancel_url=f"{front_base_url}gift-cards/buy?{cancelled_params}",
            metadata={
                "product_type": ProductType.GIFT_CARD.value,
                "coupon_ids": json.dumps([batch_price.stripe_coupon_id]),
            },
        )
        return session

    @classmethod
    def create_donation_session(
        cls,
        success_url: str,
        failure_url: str,
        donation_price: str,
        source: DonationSourceEnum,
    ) -> stripe.checkout.Session:
        params: dict[str, Any] = (
            {"api_key": settings.STRIPE_SECONDARY_API_KEY}
            if source == DonationSourceEnum.SECONDARY.value
            else {}
        )
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": donation_price,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=failure_url,
            metadata={
                "product_type": ProductType.DONATION.value,
                "source": source,
            },
            **params,
        )
        return session

    @classmethod
    def create_promo_codes(cls, coupon_ids: list[str]) -> list[str]:
        promo_codes = []
        for coupon in coupon_ids:
            promo_code = stripe.PromotionCode.create(
                coupon=coupon, code=generate_promo_code()
            )
            promo_codes.append(promo_code.get("code"))
        return promo_codes

    @classmethod
    def retrieve_customer(cls, customer_id: str) -> stripe.Customer:
        return stripe.Customer.retrieve(customer_id)

    @classmethod
    def retrieve_session(cls, session_id: str):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError:
            session = None
        return session

    @classmethod
    def _get_gift_card_line_items(cls, price_ids: list[str]) -> list:
        return [
            {
                "price": price_id,
                "quantity": 1,
            }
            for price_id in price_ids
        ]
