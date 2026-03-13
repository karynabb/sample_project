from app.core.clients.stripe_client.enums import ProductType
from app.core.enums import DonationEmailTemplateType
from app.core.sendgrid import send_donation_email

from .event_handler import EventHandler


class DonationHandler(EventHandler):
    _product_type = ProductType.DONATION

    def handle_data(self, data: dict, status: str):
        if status != "completed":
            return
        email = self._get_email(data["object"])
        name = self._get_name(data)
        source = data["object"]["metadata"].get("source")
        email_template_type = self._get_email_template_type(source)
        send_donation_email(email, name, email_template_type)

    def _get_email_template_type(self, source: str) -> DonationEmailTemplateType:
        try:
            return DonationEmailTemplateType(source)
        except ValueError:
            raise ValueError(
                f"Can't convert source {source} to DonationEmailTemplateType"
            )
