import pytest
from django.urls import reverse

from tests.constants import FAKE_ANSWERS


@pytest.mark.django_db
def test_create_draft(api_client, fake_negative_dataset):
    questionnaire_answers = FAKE_ANSWERS.copy()
    questionnaire_answers["CN1"] = fake_negative_dataset.word
    questionnaire_answers["FA"] = ["vibrant", fake_negative_dataset.word]
    url = reverse("draft_create")
    response = api_client.post(
        url, data={"answers": questionnaire_answers}, format="json"
    )
    assert response.status_code == 400
    assert "CN1" in response.json()["errors"]
    assert "FA" in response.json()["errors"]
    assert response.json()["errors"]["FA"] == ["", "bad_word"]


@pytest.mark.django_db
def test_create_questionnaire(api_client, fake_negative_dataset):
    questionnaire_answers = FAKE_ANSWERS.copy()
    questionnaire_answers["CN1"] = fake_negative_dataset.word
    url = reverse("questionnaire_create")
    response = api_client.post(
        url, data={"answers": questionnaire_answers}, format="json"
    )
    assert response.status_code == 400
    assert "CN1" in response.json()["errors"]
