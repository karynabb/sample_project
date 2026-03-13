import datetime

from django.conf import settings
from django.http import Http404
from sendgrid import Bcc, SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.email_text_templates import get_game_generation_alert_email_text
from app.core.enums import DonationEmailTemplateType
from app.core.models import Questionnaire, User

# Placeholder values for sharing; use real SendGrid template IDs in deployment.
FROM_EMAIL = "support@example.com"
TEMPLATE_NEXT_STEP = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_EXPERT_NEXT_STEP = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_RESULTS_READY = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_FAILED_INTERNAL = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_FAILED_EXTERNAL = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_GIFT_CARD = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_EXPERT_REVIEW = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_EXPERT_REVIEW_COMPLETED = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_EXPERT_PLUS_NEXT_STEP = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_EXPERT_PLUS_SEPARATE_NEXT_STEP = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_REMINDER = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_DONATION_APP = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TEMPLATE_DONATION_SECONDARY = "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def _get_env_prefix():
    env_prefix = ""
    if settings.ENVIRONMENT == "test":
        env_prefix = "test."
    elif settings.ENVIRONMENT == "acceptance":
        env_prefix = "acceptance."
    return env_prefix


def _get_donation_email_template(email_type: DonationEmailTemplateType):
    match email_type:
        case DonationEmailTemplateType.SECONDARY:
            return TEMPLATE_DONATION_SECONDARY
        case DonationEmailTemplateType.APP:
            return TEMPLATE_DONATION_APP
        case _:
            raise Http404(f"No donation email template found for type: {email_type}")


def result_ready(questionnaire: Questionnaire):
    env_prefix = _get_env_prefix()

    context = {
        "first_name": questionnaire.user.first_name,
        "last_name": questionnaire.user.last_name,
        "title": questionnaire.name,
        "id": questionnaire.id,
        "env_prefix": env_prefix,
    }
    return context


def result_ready_email(questionnaire: Questionnaire):
    context = result_ready(questionnaire)
    send_email(TEMPLATE_RESULTS_READY, context, questionnaire.user)


def next_step_email(questionnaire: Questionnaire):
    context = {
        "first_name": questionnaire.user.first_name,
        "last_name": questionnaire.user.last_name,
        "title": questionnaire.name,
    }
    send_email(TEMPLATE_NEXT_STEP, context, questionnaire.user)


def next_step_expert_email(
    questionnaire: Questionnaire, is_expert_plus_separately: bool = False
):
    context = {
        "first_name": questionnaire.user.first_name,
        "last_name": questionnaire.user.last_name,
        "title": questionnaire.name,
    }
    if is_expert_plus_separately:
        send_email(TEMPLATE_EXPERT_PLUS_SEPARATE_NEXT_STEP, context, questionnaire.user)
    elif questionnaire.expert_plus_payed:
        send_email(TEMPLATE_EXPERT_PLUS_NEXT_STEP, context, questionnaire.user)
    else:
        send_email(TEMPLATE_EXPERT_NEXT_STEP, context, questionnaire.user)


def failed_journey_internal_email(questionnaire: Questionnaire):
    context = {
        "id": questionnaire.id,
        "title": questionnaire.name,
        "user_email": questionnaire.user.email,
        "full_name": questionnaire.user.full_name,
    }
    send_internal_email(TEMPLATE_FAILED_INTERNAL, context)


def failed_journey_external_email(questionnaire: Questionnaire):
    context = {
        "title": questionnaire.name,
        "full_name": questionnaire.user.full_name,
    }
    send_email(TEMPLATE_FAILED_EXTERNAL, context, questionnaire.user)


def send_gift_card_email(email: str, full_name: str, promo_codes: tuple[str, ...]):
    message = create_email_body(
        [(email, full_name)], TEMPLATE_GIFT_CARD, {"promo_codes": promo_codes}
    )
    return send_sendgrid_message(message)


def send_expert_review_email(
    recipients: list[tuple[str, str]], batches: tuple[str, ...], is_expert_plus: bool
):
    env_prefix = _get_env_prefix()
    message = create_email_body(
        [(email, username) for email, username in recipients],
        TEMPLATE_EXPERT_REVIEW,
        {
            "batches": batches,
            "env_prefix": env_prefix,
            "is_expert_plus": is_expert_plus,
        },
    )
    return send_sendgrid_message(message)


def send_expert_review_completed_email(
    questionnaire: Questionnaire, bcc_recipients: list[str] | None = None
):
    context = result_ready(questionnaire)
    send_email(
        TEMPLATE_EXPERT_REVIEW_COMPLETED, context, questionnaire.user, bcc_recipients
    )


def send_reminder_email(user: User):
    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    send_email(TEMPLATE_REMINDER, context, user)


def send_donation_email(
    user_email: str, user_name: str, email_type: DonationEmailTemplateType
):
    template = _get_donation_email_template(email_type)
    message = create_email_body(
        [(user_email, user_name)],
        template,
    )
    return send_sendgrid_message(message)


def recipient_data(user: User) -> tuple[str, str]:
    return user.email, f"{user.first_name} {user.last_name}"


def send_internal_email(mail_template: str, context: dict):
    internal_recipient = (FROM_EMAIL, "App Support")
    message = create_email_body([internal_recipient], mail_template, context)
    return send_sendgrid_message(message)


def send_email(
    mail_template: str,
    context: dict,
    user: User,
    bcc_recipients: list[str] | None = None,
):
    message = create_email_body(
        [recipient_data(user)], mail_template, context, bcc_recipients
    )
    return send_sendgrid_message(message)


def create_email_body(
    recipients: list[tuple[str, str]] | list[str],
    template: str | None = None,
    context: dict | None = None,
    bcc_recipients: list[str] | None = None,
    body_text: str | None = None,
    subject: str | None = None,
) -> Mail:
    if template:
        message = Mail(from_email=FROM_EMAIL, to_emails=recipients)
        message.template_id = template
        if context:
            message.dynamic_template_data = context
    else:
        if not body_text:
            raise ValueError("Body text must be specified if no template is used")
        if not subject:
            subject = "no subject"
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=recipients,
            plain_text_content=body_text,
            subject=subject,
        )

    if bcc_recipients:
        for bcc_recipient in bcc_recipients:
            message.personalizations[0].add_bcc(Bcc(bcc_recipient))
    return message


def send_sendgrid_message(message: Mail):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
    return response.status_code


def send_game_generation_alert_email(game_date: datetime.date):
    text = get_game_generation_alert_email_text(game_date)
    mail = create_email_body(
        recipients=settings.ADMINS_EMAILS,
        body_text=text,
        subject="App: Game Generation Alert",
    )
    return send_sendgrid_message(mail)
