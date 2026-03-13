import logging
from contextlib import suppress
from itertools import groupby

from algorithm_library.offering_description_builder.offering_description_builder_module import (
    OfferingDescriptionBuilderModule,
)
from algorithm_library.pathways.pathways_module import PathwaysModule
from algorithm_library.phrases_builder.phrases_builder_module import (
    PhrasesBuilderModule,
)
from algorithm_library.rationale_builder.rationale_builder_module import (
    RationaleBuilder,
)
from celery.result import AsyncResult
from django.db import IntegrityError, models
from django.db.models import Q
from django.utils import timezone

from app.algorithm import constants
from app.algorithm.candidate_validators import MaxPathwayTypeValidator, PathwayType
from app.algorithm.constants import EXAMPLE_PHRASES_NUMBER
from app.algorithm.exceptions import BatchingException
from app.algorithm.models import NameCandidate, Pathway, Result, ResultBatch
from app.algorithm.utils import (
    capitalize_name,
    capitalize_rationale,
    create_cache,
    log_pathway_usage,
    retrieve_cache,
)
from app.celery import app
from app.core.models import FeatureConfig, PricingPlanName, Questionnaire
from app.core.sendgrid import result_ready_email
from app.core.utils import fail_journey
from app.expert.tasks import delegate_rationale_tasks_for_name_candidates

logger = logging.getLogger(__name__)


@app.task
def generate_name_candidates(
    questionnaire_id: int, first_run: bool = False, run_all_cascades: bool = False
):
    logger.info("Started the process of generating name candidates")
    tasks_ids = []
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    cascade_level_to_run = questionnaire.cascade_level_run + 1
    should_create_batches = True

    if run_all_cascades:
        for pathway in Pathway.objects.filter(
            active=True,
            candidates_per_batch__gt=0,
            cascade_level__gte=cascade_level_to_run,
        ):
            task = run_pathway.apply_async(
                args=[pathway.code, questionnaire_id], retries=3
            )
            tasks_ids.append(task.id)

            questionnaire.cascade_level_run = Pathway.objects.aggregate(
                models.Max("cascade_level")
            )["cascade_level__max"]
            should_create_batches = False
    else:
        for pathway in Pathway.objects.filter(
            active=True, candidates_per_batch__gt=0, cascade_level=cascade_level_to_run
        ):
            task = run_pathway.apply_async(
                args=[pathway.code, questionnaire_id], retries=3
            )
            tasks_ids.append(task.id)

        questionnaire.cascade_level_run = cascade_level_to_run
    questionnaire.save()
    check_generation_completion.delay(
        tasks_ids, questionnaire_id, first_run, should_create_batches, run_all_cascades
    )


@app.task
def run_pathway(pathway_code: str, questionnaire_id: int):
    module = PathwaysModule()
    pathway = Pathway.objects.get(code=pathway_code)
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    questionnaire_data = questionnaire.algorithm_representation

    cache = retrieve_cache(pathway, questionnaire)
    results, cache, logging_data = module.pathway_caller(
        pathway_code, questionnaire_data, cache
    )

    if cache:
        create_cache(pathway, questionnaire, cache)
    log_pathway_usage(pathway_code, questionnaire, logging_data)

    for result in results:
        with suppress(IntegrityError, ValueError):
            capitalized_result = capitalize_name(result)
            NameCandidate.objects.create(
                name=capitalized_result, pathway=pathway, questionnaire=questionnaire
            )


@app.task
def check_generation_completion(
    tasks_id: list[str],
    q_id: int,
    first_run: bool = False,
    should_create_batches: bool = True,
    run_all_cascades: bool = False,
):
    async_results = [AsyncResult(task_id) for task_id in tasks_id]
    if any(not result.ready() for result in async_results):
        check_generation_completion.apply_async(
            args=[tasks_id, q_id, first_run, should_create_batches, run_all_cascades],
            countdown=15,
        )
        return "Waiting..."
    else:
        total_pathways_run = len(tasks_id)
        failed_pathway_runs = sum(result.failed() for result in async_results)
        if total_pathways_run == 0:
            return "No tasks to run"
        percentage_failed = failed_pathway_runs / total_pathways_run * 100
        questionnaire = Questionnaire.objects.get(id=q_id)
        if percentage_failed > constants.ALLOWED_FAILURE_THRESHOLD:
            fail_journey(questionnaire)
        else:
            if should_create_batches:
                create_batch.delay(q_id, [], first_run)
            if run_all_cascades:
                on_run_all_cascades(questionnaire, q_id)


def on_run_all_cascades(questionnaire: Questionnaire, q_id: int):
    from app.core.clients.stripe_client.event_handlers import ExpertHandler
    from app.expert.models import ExpertBatchReview

    batch_reviews = ExpertBatchReview.objects.filter(
        result_batch__questionnaire=questionnaire
    )
    modified_data = []
    for batch_review in batch_reviews:
        modified_data.append(ExpertHandler.format_review_msg(batch_review))
    if modified_data:
        modified_data.insert(0, ExpertHandler.format_questionnaire_msg(questionnaire))
    delegate_rationale_tasks_for_name_candidates.delay(q_id, modified_data)


@app.task
def create_batch(
    questionnaire_id: int,
    batches_already_created: list[int],
    first_run: bool = False,
    is_additional_batch: bool = False,
):
    """
    Task to create a batch of names from candidates. If the number of candidates is insufficient,
    it handles the process differently based on whether batches were already created or not.
    """
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    name_candidates = NameCandidate.objects.filter(questionnaire=questionnaire)

    if name_candidates.count() <= FeatureConfig.get_active_config().batch_size:
        handle_insufficient_candidates(
            batches_already_created, questionnaire_id, first_run, is_additional_batch
        )
        return

    new_batch = create_and_configure_batch(
        questionnaire,
        batches_already_created,
        questionnaire_id,
        first_run,
        is_additional_batch,
    )
    if not new_batch:
        return

    batches_already_created.append(new_batch.id)
    manage_batches(
        batches_already_created, questionnaire_id, first_run, is_additional_batch
    )


def handle_insufficient_candidates(
    batches_already_created, questionnaire_id, first_run, is_additional_batch
):
    """
    Handles the scenario where there are not enough name candidates to create a new batch.
    Either triggers a task to generate new name candidates or delegates rationale tasks.
    """
    if not batches_already_created:
        generate_name_candidates.delay(questionnaire_id, first_run)
    else:
        delegate_rationale_tasks.delay(batches_already_created, questionnaire_id)


def create_and_configure_batch(
    questionnaire,
    batches_already_created,
    questionnaire_id,
    first_run,
    is_additional_batch,
):
    """
    Attempts to create and configure a new batch.
    Handles exceptions and returns the new batch or None.
    """
    new_batch = ResultBatch.objects.create(questionnaire=questionnaire)
    try:
        configure_batch_if_required(new_batch)
        new_batch.make_from_candidates()
        return new_batch
    except BatchingException:
        new_batch.delete()
        if batches_already_created:
            delegate_rationale_tasks.delay(
                batches_already_created,
                questionnaire_id,
            )
        else:
            generate_name_candidates.delay(questionnaire_id, first_run)
        return None


def configure_batch_if_required(batch):
    """
    Configures the batch with validators if the pricing plan requires it.
    """
    if FeatureConfig.get_active_config().pricing_plan == PricingPlanName.B:
        batch.candidate_validators.extend(
            [
                MaxPathwayTypeValidator(
                    max_candidates=1, pathway_type=PathwayType.COINED
                ),
                MaxPathwayTypeValidator(
                    max_candidates=1, pathway_type=PathwayType.DOUBLE
                ),
            ]
        )


def manage_batches(
    batches_already_created, questionnaire_id, first_run, is_additional_batch
):
    """
    Manages created batches by either delegating rationale tasks or creating more batches,
    based on the count.
    """

    if batches_already_created:
        delegate_rationale_tasks.delay(batches_already_created, questionnaire_id)
        if first_run:
            create_batch.delay(questionnaire_id, [], False, True)
    else:
        create_batch.delay(questionnaire_id, batches_already_created, first_run)


@app.task
def delegate_rationale_tasks(
    batch_ids: list[int],
    q_id: int,
):
    rationale_tasks_started = []
    for batch_id in batch_ids:
        task = generate_rationales.apply_async(args=[batch_id], retries=3)
        rationale_tasks_started.append(task.id)
    check_rationales_completion.delay(rationale_tasks_started, q_id, batch_ids)


@app.task
def generate_rationales(batch_id: int):
    results_qs = Result.objects.filter(rationale="", batch__id=batch_id).select_related(
        "pathway"
    )
    batch = ResultBatch.objects.get(id=batch_id)

    for pathway_code, group in groupby(results_qs, lambda x: x.pathway.code):
        results = list(group)
        module = RationaleBuilder(batch.questionnaire.algorithm_representation)
        results_names = [result.name for result in results]
        rationale_result: dict = module.run(results_names, pathway_code)

        for result in results:
            capitalized_name = capitalize_name(name=result.name)
            result_dict = rationale_result.get(capitalized_name, {})
            rationale = result_dict.get("Rationale")
            if rationale:
                capitalized_rationale = capitalize_rationale(
                    name=result.name, rationale=rationale
                )
                result.rationale = capitalized_rationale
                result.save()


@app.task
def check_rationales_completion(
    tasks_id: list[str],
    q_id: int,
    batch_ids: list[int],
):
    async_results = [AsyncResult(task_id) for task_id in tasks_id]
    if any(not result.ready() for result in async_results):
        check_rationales_completion.apply_async(
            args=[tasks_id, q_id, batch_ids], countdown=6
        )
        return "Waiting for rationales generation..."
    else:
        phrases_tasks_started = []
        for batch_id in batch_ids:
            phrases_task = generate_result_phrases.apply_async(
                args=[batch_id], retries=3
            )
            phrases_tasks_started.append(phrases_task.id)
        check_phrases_completion.apply_async(args=[tasks_id, q_id], countdown=6)


@app.task
def generate_offering_description(questionnaire_id: int):
    questionnaire = Questionnaire.objects.get(id=questionnaire_id)
    questionnaire_data = questionnaire.algorithm_representation

    offering_description_module = OfferingDescriptionBuilderModule()

    description = offering_description_module.run(questionnaire_data)

    if description:
        questionnaire.set_offering_description(description)
    else:
        logger.error(
            f"No description was generated for questionnaire {questionnaire_id}"
        )
        raise Exception("No description was generated")


@app.task
def check_phrases_completion(
    tasks_id: list[str],
    q_id: int,
):
    questionnaire = Questionnaire.objects.get(id=q_id)
    async_results = [AsyncResult(task_id) for task_id in tasks_id]
    if any(not result.ready() for result in async_results):
        check_phrases_completion.apply_async(args=[tasks_id, q_id], countdown=6)
        return "Waiting for phrases generation..."
    else:
        batches_created = ResultBatch.objects.filter(questionnaire=questionnaire)

        for batch in batches_created:
            batch.visible = True
            if (
                not batch.results.filter(rationale="").exists()
                and not ResultBatch.objects.filter(
                    questionnaire=questionnaire, bought=True
                ).exists()
            ):
                batch.bought = True
                batch.bought_timestamp = timezone.now()
                result_ready_email(questionnaire)
            batch.save()
        generate_offering_description.delay(q_id)


@app.task
def generate_result_phrases(batch_id: int):
    results_qs = Result.objects.filter(
        Q(example_phrases__isnull=True) | Q(example_phrases=[]), batch__id=batch_id
    )
    batch = ResultBatch.objects.get(id=batch_id)
    phrases_builder_module = PhrasesBuilderModule(
        batch.questionnaire.algorithm_representation
    )
    for result in results_qs:
        phrases = phrases_builder_module.run(result.name, result.rationale)
        if not phrases or len(phrases) < EXAMPLE_PHRASES_NUMBER:
            logger.error(f"No phrases were generated for result {result.name}")
        else:
            result.example_phrases = phrases[:EXAMPLE_PHRASES_NUMBER]
            result.save()
            logger.info(f"Example phrases generated for result {result.name}")
