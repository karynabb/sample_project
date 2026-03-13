from app.algorithm.candidate_validators import MaxPathwayTypeValidator, PathwayType
from app.algorithm.models import NameCandidate, Pathway


def test_validate__different_pathway_type(fake_questionnaire):
    validator = MaxPathwayTypeValidator(
        max_candidates=1, pathway_type=PathwayType.COINED
    )

    pathway = Pathway(code="some_code", global_rationale="")
    name_candidate = NameCandidate(
        name="test", pathway=pathway, questionnaire=fake_questionnaire
    )

    assert validator.validate(name_candidate)
    assert validator._current_amount == 0


def test_validate__same_pathway_type(fake_questionnaire):
    validator = MaxPathwayTypeValidator(
        max_candidates=1, pathway_type=PathwayType.COINED
    )

    pathway = Pathway(code="coined_1", global_rationale="")
    name_candidate = NameCandidate(
        name="test", pathway=pathway, questionnaire=fake_questionnaire
    )

    assert validator.validate(name_candidate)
    assert validator._current_amount == 1


def test_validate__exceeds_amount(fake_questionnaire):
    validator = MaxPathwayTypeValidator(
        max_candidates=0, pathway_type=PathwayType.COINED
    )

    pathway = Pathway(code="coined_1", global_rationale="")
    name_candidate = NameCandidate(
        name="test", pathway=pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(name_candidate)
    assert validator._current_amount == 0


def test_reset(fake_questionnaire):
    validator = MaxPathwayTypeValidator(
        max_candidates=1, pathway_type=PathwayType.COINED
    )
    validator._current_amount = 1

    pathway = Pathway(code="coined_1", global_rationale="")
    name_candidate = NameCandidate(
        name="test", pathway=pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(name_candidate)
    assert validator._current_amount == 1

    validator.reset()
    assert validator._current_amount == 0
    assert validator.validate(name_candidate)
    assert validator._current_amount == 1
