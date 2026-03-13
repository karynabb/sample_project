import pytest
from django.urls import reverse

from app.core.models import DraftQuestionnaire, Questionnaire
from tests.constants import FAKE_ANSWERS


@pytest.mark.django_db
def test_completion(api_client, fake_draft_questionnaire):
    url = reverse("complete_draft", kwargs={"id": fake_draft_questionnaire.id})
    assert Questionnaire.objects.count() == 0
    assert DraftQuestionnaire.objects.count() == 1
    response = api_client.post(url)
    assert response.status_code == 200
    assert Questionnaire.objects.count() == 1
    assert DraftQuestionnaire.objects.count() == 0


@pytest.mark.django_db
def test_parent_transition(api_client, fake_draft_questionnaire, fake_user):
    parent_questionnaire = Questionnaire.objects.create(
        user=fake_user, answers=FAKE_ANSWERS
    )
    fake_draft_questionnaire.parent = parent_questionnaire
    fake_draft_questionnaire.save()
    url = reverse("complete_draft", kwargs={"id": fake_draft_questionnaire.id})
    response = api_client.post(url)
    assert response.status_code == 200
    assert response.json()["parent"] == parent_questionnaire.id
