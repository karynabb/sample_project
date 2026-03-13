from app.algorithm.candidate_validators import UniqueNameValidator
from app.algorithm.models import NameCandidate


def test_validate__valid__first_word(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()

    candidate = NameCandidate(
        name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert validator.validate(candidate)
    assert validator._added_words == {"abc"}


def test_is_valid_name__valid__first_double(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()

    candidate = NameCandidate(
        name="abc abc", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert validator.validate(candidate)
    assert validator._added_words == {"abc"}


def test_is_valid_name__valid__single(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"bcd", "zab"}

    candidate = NameCandidate(
        name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert validator.validate(candidate)
    assert validator._added_words == {"bcd", "zab", "abc"}


def test_is_valid_name__valid__double(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"zab", "bcd", "cde", "efg"}

    candidate = NameCandidate(
        name="abc def", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert validator.validate(candidate)
    assert validator._added_words == {"zab", "bcd", "cde", "efg", "abc", "def"}


def test_is_valid_name__invalid__single_subword(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"abcd"}

    candidate = NameCandidate(
        name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"abcd"}


def test_is_valid_name__invalid__single_superword(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"abc"}

    candidate = NameCandidate(
        name="abcd", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"abc"}


def test_is_valid_name__invalid__double_subword(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"abcd"}

    candidate = NameCandidate(
        name="abc def", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"abcd"}


def test_is_valid_name__invalid__double_superword(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"abc"}

    candidate = NameCandidate(
        name="abcd efgh", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"abc"}


def test_is_valid_name__invalid__single_exact_match(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"abc"}

    candidate = NameCandidate(
        name="abc", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"abc"}


def test_is_valid_name__invalid__double_exact_match(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"def"}

    candidate = NameCandidate(
        name="abc def", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"def"}


def test_reset(fake_pathway, fake_questionnaire):
    validator = UniqueNameValidator()
    validator._added_words = {"def"}

    candidate = NameCandidate(
        name="abc def", pathway=fake_pathway, questionnaire=fake_questionnaire
    )

    assert not validator.validate(candidate)
    assert validator._added_words == {"def"}

    validator.reset()

    assert validator._added_words == set()
    assert validator.validate(candidate)
    assert validator._added_words == {"abc", "def"}
