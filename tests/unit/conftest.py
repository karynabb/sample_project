import pytest

from app.algorithm.models import Pathway
from app.core.models import Payment, Questionnaire, User
from tests.constants import FAKE_ANSWERS


@pytest.fixture
def fake_user(username: str = "test_user") -> User:
    return User(username=username)


@pytest.fixture
def fake_questionnaire(fake_user: User) -> Questionnaire:
    return Questionnaire(user=fake_user, answers=FAKE_ANSWERS)


@pytest.fixture
def fake_pathway() -> Pathway:
    return Pathway(code="test_code", global_rationale="test_rationale")


@pytest.fixture
def fake_payment(fake_questionnaire) -> Payment:
    return Payment(
        user=fake_questionnaire.user,
        questionnaire=fake_questionnaire,
        checkout_url="test_url",
        payment_type="initial",
    )
