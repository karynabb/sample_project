import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create(api_client, fake_draft_questionnaire):
    url = reverse("create_questionnaire_event")
    data = {
        "type": "questionnaire_next",
        "timestamp": "2021-08-30T13:58:18.896Z",
        "draft": fake_draft_questionnaire.id,
    }
    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 201

    data["type"] = "questionnaire_prev"
    response = api_client.post(url, data=data, format="json")
    assert response.status_code == 201
