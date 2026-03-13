import pytest

from app.algorithm.models import NameCandidate


@pytest.mark.django_db
def test_names_unique__already_in_results(fake_batch, fake_pathway):
    fake_batch.add_result("test", "test", fake_pathway)
    with pytest.raises(ValueError):
        NameCandidate.objects.create(
            name="test", pathway=fake_pathway, questionnaire=fake_batch.questionnaire
        )


@pytest.mark.django_db
def test_names_unique__already_in_candidates(fake_candidate):
    with pytest.raises(ValueError):
        NameCandidate.objects.create(
            name=fake_candidate.name,
            pathway=fake_candidate.pathway,
            questionnaire=fake_candidate.questionnaire,
        )
