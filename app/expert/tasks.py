import logging
from itertools import groupby

from algorithm_library.rationale_builder.rationale_builder_module import (
    RationaleBuilder,
)
from celery.result import AsyncResult
from django.conf import settings

from app.algorithm.models import NameCandidate
from app.algorithm.utils import capitalize_name, capitalize_rationale
from app.celery import app
from app.core.models import Questionnaire
from app.core.sendgrid import (
    next_step_expert_email,
    send_expert_review_completed_email,
    send_expert_review_email,
)

logger = logging.getLogger(__name__)


@app.task(
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def sendgrid_send_expert_review_required_card(
    recipients: list[tuple[str, str]], batches: list[str], is_expert_plus: bool
):
    send_expert_review_email(recipients, tuple(batches), is_expert_plus)


@app.task(
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def sendgrid_send_expert_review_completed_card(
    questionnaire_id: int,
):
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    send_expert_review_completed_email(
        questionnaire, settings.BCC_RECIPIENTS_EXPERT_REVIEW
    )


@app.task(
    max_retries=5,
    retry_backoff=10,
    retry_jitter=True,
)
def sendgrid_send_expert_next_step_card(
    questionnaire_id: int, is_expert_plus_separately: bool = False
):
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)

    next_step_expert_email(questionnaire, is_expert_plus_separately)


@app.task
def generate_rationales_for_name_candidates(questionnaire_id: int):
    logger.info(f"Generating rationales for questionnaire: {questionnaire_id}")
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    name_candidates = NameCandidate.objects.filter(
        questionnaire=questionnaire
    ).select_related("pathway")

    for pathway_code, group in groupby(name_candidates, lambda x: x.pathway.code):
        name_candidates_group = list(group)
        module = RationaleBuilder(questionnaire.algorithm_representation)
        results_names = [
            name_candidate.name for name_candidate in name_candidates_group
        ]
        rationale_result: dict = module.run(results_names, pathway_code)

        for name_candidate in name_candidates_group:
            capitalized_name = capitalize_name(name=name_candidate.name)
            result_dict = rationale_result.get(capitalized_name, {})
            rationale = result_dict.get("Rationale")
            if rationale:
                logger.info(f"Rationale for {capitalized_name}: {rationale}")
                capitalized_rationale = capitalize_rationale(
                    name=name_candidate.name, rationale=rationale
                )
                try:
                    existing_candidate = NameCandidate.objects.get(
                        name=capitalized_name, questionnaire=questionnaire
                    )
                    existing_candidate.rationale = capitalized_rationale
                    existing_candidate.clean_fields(
                        exclude=["rationale"]
                    )  # Validate all fields except 'rationale'
                    logger.info(f"Updating rationale for {capitalized_name}")
                    existing_candidate.save()

                except NameCandidate.DoesNotExist:
                    logger.info(f"Creating new name candidate: {capitalized_name}")
                    NameCandidate.objects.create(
                        name=capitalized_name,
                        rationale=capitalized_rationale,
                        questionnaire=questionnaire,
                    )
                except Exception as e:
                    logger.info(f"Error updating name candidate: {e}")


@app.task
def check_rationales_completion_for_name_candidates(
    task_id: str, q_id: int, modified_data: list[str] = []
):
    from app.core.clients.stripe_client.event_handlers import ExpertHandler

    logger.info(f"Checking rationales completion for questionnaire: {q_id}")
    questionnaire = Questionnaire.objects.get(id=q_id)
    async_result = AsyncResult(task_id)
    if not async_result.ready():
        logger.info("Rationale generation not ready yet")
        check_rationales_completion_for_name_candidates.apply_async(
            args=[task_id, q_id, modified_data], countdown=6
        )
        return "Waiting..."
    else:
        logger.info("Rationale generation ready")
        name_candidates = NameCandidate.objects.filter(questionnaire=questionnaire)

        for name_candidate in name_candidates:
            if not name_candidate.rationale:
                continue

        recipients = ExpertHandler.get_expert_email_recipients()

        sendgrid_send_expert_review_required_card.delay(
            recipients, modified_data, is_expert_plus=True
        )


@app.task
def delegate_rationale_tasks_for_name_candidates(
    q_id: int, modified_data: list[str] = []
):
    logger.info(f"Delegating rationale tasks for questionnaire: {q_id}")
    rationale_task = generate_rationales_for_name_candidates.apply_async(
        args=[q_id], retries=3
    )
    rationale_task_id = rationale_task.id
    check_rationales_completion_for_name_candidates.apply_async(
        args=[rationale_task_id, q_id, modified_data], countdown=6
    )
