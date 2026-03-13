import uuid

import pytest

from app.algorithm.models import (
    NameCandidate,
    NegativeDataset,
    Pathway,
    Result,
    ResultBatch,
)
from app.core.models import (
    DraftQuestionnaire,
    Payment,
    PricingPlan,
    PricingPlanName,
    Questionnaire,
    User,
)
from tests.constants import FAKE_ANSWERS


@pytest.fixture
def fake_user(username: str | None = None):
    if username is None:
        username = str(uuid.uuid4())
    user = User.objects.create(username=username)
    yield user
    user.delete()


@pytest.fixture
def fake_draft_questionnaire(fake_user: User):
    questionnaire = DraftQuestionnaire.objects.create(
        user=fake_user, answers=FAKE_ANSWERS
    )
    yield questionnaire
    questionnaire.delete()


@pytest.fixture
def fake_questionnaire(fake_user: User):
    questionnaire = Questionnaire.objects.create(user=fake_user, answers=FAKE_ANSWERS)
    yield questionnaire
    questionnaire.delete()


@pytest.fixture
def fake_batch(fake_questionnaire):
    batch = ResultBatch.objects.create(
        questionnaire=fake_questionnaire,
    )
    yield batch
    batch.delete()


@pytest.fixture
def fake_result(fake_batch, fake_pathway):
    result = Result.objects.create(
        name=str(uuid.uuid4()),
        rationale=str(uuid.uuid4()),
        batch=fake_batch,
        feedback=0,
        pathway=fake_pathway,
    )
    yield result
    result.delete()


@pytest.fixture
def fake_pathway():
    pathway = Pathway.objects.create(
        code="test_code", global_rationale="test_rationale"
    )
    yield pathway
    pathway.delete()


@pytest.fixture
def fake_candidate(fake_questionnaire, fake_pathway):
    candidate = NameCandidate.objects.create(
        name=str(uuid.uuid4()), questionnaire=fake_questionnaire, pathway=fake_pathway
    )
    yield candidate
    candidate.delete()


@pytest.fixture
def fake_payment(fake_questionnaire):
    payment = Payment.objects.create(
        user=fake_questionnaire.user,
        questionnaire=fake_questionnaire,
        checkout_url="test_url",
        payment_type="initial",
    )
    yield payment
    payment.delete()


@pytest.fixture
def fake_pricing_plan():
    pricing_plan = PricingPlan.objects.create(name=PricingPlanName.A)
    yield pricing_plan
    pricing_plan.delete()


@pytest.fixture
def fake_negative_dataset():
    negative_dataset = NegativeDataset.objects.create(word="bad_word")
    yield negative_dataset
    negative_dataset.delete()
