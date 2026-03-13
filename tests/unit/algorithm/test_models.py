import uuid
from unittest.mock import MagicMock, patch

from django.db.models import QuerySet

from app.algorithm.models import NameCandidate, Pathway, ResultBatch
from app.core.models import Config, FeatureConfig, PricingPlanName, Questionnaire


def test_construct_batch__empty(fake_questionnaire: Questionnaire):
    result_batch = ResultBatch(questionnaire=fake_questionnaire)
    assert result_batch._construct_candidates_batch([]) == []


@patch.object(QuerySet, "first")
def test_construct_candidates_batch__single_candidate(
    first_mock: MagicMock, fake_questionnaire: Questionnaire, fake_pathway: Pathway
):
    first_mock.return_value = FeatureConfig(
        version="1",
        active=True,
        values=Config(pricing_plan=PricingPlanName.A, batch_size=24),
    )

    result_batch = ResultBatch(questionnaire=fake_questionnaire)
    candidates = [
        NameCandidate(
            name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
        )
    ]
    candidates_batch = result_batch._construct_candidates_batch(candidates)

    assert len(candidates_batch) == 1
    assert candidates_batch[0].name == "abc"


@patch.object(QuerySet, "first")
def test_construct_candidates_batch__invalid_candidate(
    first_mock: MagicMock, fake_questionnaire: Questionnaire, fake_pathway: Pathway
):
    first_mock.return_value = FeatureConfig(
        version="1",
        active=True,
        values=Config(pricing_plan=PricingPlanName.A, batch_size=24),
    )

    result_batch = ResultBatch(questionnaire=fake_questionnaire)
    candidates = [
        NameCandidate(
            name="abcd", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
        NameCandidate(
            name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
    ]

    candidates_batch = result_batch._construct_candidates_batch(candidates)

    assert len(candidates_batch) == 1
    assert candidates_batch[0].name == "abcd"


@patch.object(QuerySet, "first")
def test_construct_candidates_batch__multiple_candidates(
    first_mock: MagicMock, fake_questionnaire: Questionnaire, fake_pathway: Pathway
):
    first_mock.return_value = FeatureConfig(
        version="1",
        active=True,
        values=Config(pricing_plan=PricingPlanName.A, batch_size=24),
    )

    result_batch = ResultBatch(questionnaire=fake_questionnaire)
    candidates = [
        NameCandidate(
            name="abcd", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
        NameCandidate(
            name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
        NameCandidate(
            name="def", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
    ]

    candidates_batch = result_batch._construct_candidates_batch(candidates)

    assert len(candidates_batch) == 2
    assert candidates_batch[0].name == "abcd"
    assert candidates_batch[1].name == "def"


@patch.object(QuerySet, "first")
def test_construct_candidates_batch__not_exceeds_batch_size(
    first_mock: MagicMock, fake_questionnaire: Questionnaire, fake_pathway: Pathway
):
    first_mock.return_value = FeatureConfig(
        version="1",
        active=True,
        values=Config(pricing_plan=PricingPlanName.A, batch_size=24),
    )

    result_batch = ResultBatch(questionnaire=fake_questionnaire)
    candidates = [
        NameCandidate(
            name=str(uuid.uuid4()),
            pathway=fake_pathway,
            questionnaire=fake_questionnaire,
        )
        for _ in range(FeatureConfig.get_active_config().batch_size + 5)
    ]

    candidates_batch = result_batch._construct_candidates_batch(candidates)

    assert len(candidates_batch) == FeatureConfig.get_active_config().batch_size


def test_construct_results_batch(
    fake_questionnaire: Questionnaire, fake_pathway: Pathway
):
    result_batch = ResultBatch(questionnaire=fake_questionnaire)
    candidates_batch = [
        NameCandidate(
            name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
        NameCandidate(
            name="def", pathway=fake_pathway, questionnaire=fake_questionnaire
        ),
    ]

    results_batch = result_batch._construct_results_batch(candidates_batch)

    assert len(results_batch) == len(candidates_batch)
    assert results_batch[0].name == candidates_batch[0].name
    assert results_batch[1].name == candidates_batch[1].name
