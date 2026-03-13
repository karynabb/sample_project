from app.core.models import Payment

from ..enums import ProductType
from .event_handler import EventHandler


class BatchHandler(EventHandler):
    _product_type = ProductType.BATCH

    def handle_data(self, data: dict, status: str):
        from app.core.tasks import create_hubspot_deal

        checkout_id = data["object"]["id"]
        payment = Payment.objects.select_related("user").get(stripe_id=checkout_id)
        payment.status = status
        payment.save()

        if status == "completed":
            amount_total = data["object"].get("amount_total")
            create_hubspot_deal.delay(
                payment.user.email, payment.payment_type, amount_total
            )
