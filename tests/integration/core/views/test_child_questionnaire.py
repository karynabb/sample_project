import pytest
from django.urls import reverse

from app.core.models import DraftQuestionnaire, Questionnaire
from tests.constants import FAKE_ANSWERS


@pytest.mark.django_db
def test_create_child(api_client, fake_questionnaire):
    url = reverse("questionnaire_create_child", kwargs={"id": fake_questionnaire.id})

    assert DraftQuestionnaire.objects.count() == 0
    response = api_client.post(url)
    assert response.status_code == 200
    expected_keys = ["RA", "N1", "offering"]
    assert all(key in response.json()["answers"].keys() for key in expected_keys)
    assert response.json()["parent"] == fake_questionnaire.id
    assert DraftQuestionnaire.objects.count() == 1


@pytest.mark.django_db
def test_create_child_wrong_user(api_client, fake_questionnaire, wrong_authed_user):
    url = reverse("questionnaire_create_child", kwargs={"id": fake_questionnaire.id})
    response = api_client.post(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_naming_children(api_client, fake_questionnaire, fake_user):
    url = reverse("questionnaire_create_child", kwargs={"id": fake_questionnaire.id})
    parent_name = fake_questionnaire.name
    first_response = api_client.post(url)
    assert first_response.status_code == 200
    assert first_response.json()["name"] == f"{parent_name} - 1"
    second_response = api_client.post(url)
    assert second_response.status_code == 200
    assert second_response.json()["name"] == f"{parent_name} - 2"

    # Create a "complete" child for parent
    complete_child = Questionnaire.objects.create(
        user=fake_user,
        answers=FAKE_ANSWERS,
        parent=fake_questionnaire,
    )
    # Create a child of a child, expected to be named 4
    # since there are 3 children of a parent
    new_url = reverse("questionnaire_create_child", kwargs={"id": complete_child.id})
    third_response = api_client.post(new_url)
    assert third_response.status_code == 200
    assert third_response.json()["name"] == f"{parent_name} - 4"
    assert third_response.json()["parent"] == fake_questionnaire.id
