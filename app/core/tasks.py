import logging

from hubspot.crm import contacts, deals

from app.celery import app
from app.core.clients.hubspot_client.client import hubspot_client
from app.core.clients.hubspot_client.enums import LifecycleStage
from app.core.clients.hubspot_client.exceptions import ContactDoesNotExistException
from app.core.clients.stripe_client.client import StripeClient
from app.core.models import Payment, User
from app.core.sendgrid import (
    send_gift_card_email,
    send_reminder_email,
)

logger = logging.getLogger(__name__)


@app.task(
    autoretry_for=(contacts.ApiException,),
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def create_hubspot_contact(email: str, first_name: str, last_name: str):
    hubspot_client.create_contact(email, first_name, last_name)


@app.task(
    autoretry_for=(contacts.ApiException,),
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def create_hubspot_contact_for_gift_card(email: str):
    hubspot_client.create_contact(email)


@app.task(
    autoretry_for=(
        contacts.ApiException,
        deals.ApiException,
        ContactDoesNotExistException,
    ),
    max_retries=10,
    retry_backoff=3,
    retry_jitter=True,
)
def create_hubspot_deal(email: str, payment_type: str, amount: int):
    hubspot_client.create_deal(email, payment_type, amount)


@app.task(
    autoretry_for=(contacts.ApiException,),
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def update_hubspot_client_to_opportunity(user_id: int):
    user = User.objects.get(id=user_id)
    if Payment.objects.filter(user__pk=user_id, status="completed").exists():
        # If has a successful payment then already should be a Customer:
        # changing stage to Opportunity would be a downgrade
        return
    hubspot_client.update_lifecycle_stage(user.email, LifecycleStage.OPPORTUNITY)


@app.task(
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def create_stripe_promo_codes(email: str, full_name: str, coupon_ids: list[str]):
    promo_codes = StripeClient.create_promo_codes(coupon_ids)
    sendgrid_send_gift_card_email.delay(email, full_name, promo_codes)


@app.task(
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def sendgrid_send_gift_card_email(email: str, full_name: str, promo_codes: list[str]):
    send_gift_card_email(email, full_name, tuple(promo_codes))


@app.task(
    name="schedule_sendgrid_send_reminder_email",
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def schedule_sendgrid_send_reminder_email():
    """Sending reminder email to users who haven't completed the questionnaire
    and has not received a reminder email and has no payments."""
    user_ids = User.objects.filter(
        reminder_email_sent=False, payments__isnull=True
    ).values_list("id", flat=True)
    for user_id in user_ids:
        user = User.objects.get(id=user_id)
        if user.questionnaires.exists() or user.drafts.exists():
            sendgrid_send_reminder_email.delay(user_id)


@app.task(
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def sendgrid_send_reminder_email(user_id):
    user = User.objects.get(id=user_id)
    send_reminder_email(user)
    user.reminder_email_sent = True
    user.save()
