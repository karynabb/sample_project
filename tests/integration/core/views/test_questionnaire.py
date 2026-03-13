import pytest
from django.urls import reverse

from tests.constants import FAKE_ANSWERS


@pytest.mark.django_db
def test_get(api_client, fake_questionnaire):
    url = reverse("questionnaire_detail", kwargs={"id": fake_questionnaire.id})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["answers"] == fake_questionnaire.answers


@pytest.mark.django_db
def test_create(api_client):
    url = reverse("questionnaire_create")
    response = api_client.post(url, data={"answers": FAKE_ANSWERS}, format="json")
    assert response.status_code == 201


@pytest.mark.django_db
def test_update(api_client, fake_questionnaire):
    url = reverse("questionnaire_detail", kwargs={"id": fake_questionnaire.id})
    new_answers = {
        **FAKE_ANSWERS,
        "N1": "test",
        "offering": "i like trains",
    }
    assert fake_questionnaire.name != "updated_name"
    response = api_client.patch(
        url, data={"answers": new_answers, "name": "updated_name"}, format="json"
    )
    assert response.status_code == 200
    assert response.json()["answers"]["N1"] == "test"
    assert response.json()["answers"]["offering"] == "i like trains"
    assert response.json()["name"] == "updated_name"


@pytest.mark.django_db
def test_delete(api_client, fake_questionnaire):
    url = reverse("questionnaire_detail", kwargs={"id": fake_questionnaire.id})
    response = api_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_delete_wrong_owner(api_client, fake_questionnaire, wrong_authed_user):
    url = reverse("questionnaire_detail", kwargs={"id": fake_questionnaire.id})
    response = api_client.delete(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_listview(api_client, fake_questionnaire):
    url = reverse("questionnaire_list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert "next" in response.json()
    assert "previous" in response.json()


@pytest.mark.django_db
def test_has_result(api_client, fake_result):
    fake_result.batch.bought = True
    fake_result.batch.save()
    url = reverse(
        "questionnaire_detail", kwargs={"id": fake_result.batch.questionnaire.id}
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["has_results"] is True
