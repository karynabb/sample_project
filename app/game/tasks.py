import logging
from datetime import date, datetime, timedelta

from django.db.models import Q

from app.algorithm.tasks import generate_offering_description, generate_rationales
from app.celery import app
from app.core.models import Questionnaire
from app.core.sendgrid import send_game_generation_alert_email
from app.game.exceptions import GameGenerationError
from app.game.models import GameConfig
from app.game.services.game_creation_service import GameCreationService

logger = logging.getLogger(__name__)


@app.task
def bulk_generate_rationale_offering_description(limit: int):
    questionnaires_qs = Questionnaire.objects.filter(
        Q(offering_description="") | Q(offering_description__isnull=True)
    )[:limit]
    logger.info(
        f"Generating offering description and rationales for {questionnaires_qs.count()} "
        f"questionnaires"
    )
    for questionnaire in questionnaires_qs:
        logger.info(
            f"Generating offering description and rationales for questionnaire {questionnaire.id}"
        )
        generate_offering_description.delay(questionnaire.id)
        for batch in questionnaire.result_batches.all():
            generate_rationales.delay(batch.id)


@app.task
def sendgrid_send_alert_email(game_date: date):
    send_game_generation_alert_email(game_date)


@app.task
def generate_games(
    start_date: datetime, end_date: datetime, override_game: bool = True
):
    if start_date is None:
        start_date = datetime.today().date()
    if end_date is None:
        end_date = datetime.today().date() + timedelta(weeks=1)

    game_config = GameConfig.objects.filter(is_active=True).first()
    if not game_config:
        raise ValueError("No active game configuration found.")

    current_date = start_date
    try:
        while current_date <= end_date:
            GameCreationService.create_game_with_error_retries(
                game_config=game_config, date=current_date, override_game=override_game
            )
            current_date += timedelta(days=1)
    except GameGenerationError as e:
        logger.error(f"Error in games generation: {e}")
        sendgrid_send_alert_email.delay(current_date)
        return


@app.task(name="schedule_generate_games")
def schedule_generate_games():
    start_date = datetime.today().date()
    end_date = datetime.today().date() + timedelta(weeks=2)
    generate_games.delay(start_date=start_date, end_date=end_date, override_game=False)
