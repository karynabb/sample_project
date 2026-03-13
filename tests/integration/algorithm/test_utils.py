import pytest

from app.algorithm.models import NameCandidate
from app.algorithm.utils import candidates_from_pathway


@pytest.mark.django_db
def test_candidates_from_pathway(fake_pathway, fake_questionnaire):
    candidate1 = NameCandidate.objects.create(
        name="test1", pathway=fake_pathway, questionnaire=fake_questionnaire
    )
    candidate2 = NameCandidate.objects.create(
        name="test2", pathway=fake_pathway, questionnaire=fake_questionnaire
    )
    fake_pathway.candidates_per_batch = 1
    fake_pathway.save()
    results = candidates_from_pathway(fake_pathway, fake_questionnaire)
    assert len(results) == 1
    candidate1.delete()
    candidate2.delete()
