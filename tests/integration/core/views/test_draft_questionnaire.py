import pytest
from django.urls import reverse

from tests.constants import FAKE_ANSWERS


@pytest.mark.django_db
def test_get(api_client, fake_draft_questionnaire):
    url = reverse("draft_detail", kwargs={"id": fake_draft_questionnaire.id})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["answers"] == fake_draft_questionnaire.answers


@pytest.mark.django_db
def test_create(api_client):
    url = reverse("draft_create")
    response = api_client.post(url, data={"answers": FAKE_ANSWERS}, format="json")
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_bad_schema(api_client):
    url = reverse("draft_create")
    response = api_client.post(url, data={"answers": {"igor": "igor"}}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_update(api_client, fake_draft_questionnaire):
    url = reverse("draft_detail", kwargs={"id": fake_draft_questionnaire.id})
    new_answers = {
        **fake_draft_questionnaire.answers,
        "N1": "test",
        "offering": "i dont like trains",
    }
    assert fake_draft_questionnaire.name != "updated_name"
    response = api_client.patch(
        url,
        data={
            "answers": new_answers,
            "name": "updated_name",
            "last_edited_question": 3,
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["answers"]["N1"] == "test"
    assert response.json()["answers"]["offering"] == "i dont like trains"
    assert response.json()["name"] == "updated_name"
    assert response.json()["last_edited_question"] == 3


@pytest.mark.django_db
def test_delete(api_client, fake_draft_questionnaire):
    url = reverse("draft_detail", kwargs={"id": fake_draft_questionnaire.id})
    response = api_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_delete_wrong_owner(api_client, fake_draft_questionnaire, wrong_authed_user):
    url = reverse("draft_detail", kwargs={"id": fake_draft_questionnaire.id})
    response = api_client.delete(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_listview(api_client, fake_draft_questionnaire):
    url = reverse("draft_list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert "next" in response.json()
    assert "previous" in response.json()
    assert "id" in response.json()["results"][0]
