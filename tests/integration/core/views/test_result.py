import pytest
from django.urls import reverse

from app.algorithm.models import Pathway, Result, ResultBatch


def create_results(batch: ResultBatch, pathway: Pathway):
    return [
        Result.objects.create(
            name=f"test{i}",
            rationale="test",
            batch=batch,
            feedback=i,
            pathway=pathway,
            favorite=i == 1,
        )
        for i in range(1, 4)
    ]


@pytest.mark.django_db
@pytest.fixture(autouse=True)
def create_batches(fake_questionnaire, fake_pathway):
    batch1 = ResultBatch.objects.create(
        questionnaire=fake_questionnaire, bought=True, visible=True
    )
    results1 = create_results(batch1, fake_pathway)
    batch2 = ResultBatch.objects.create(
        questionnaire=fake_questionnaire, bought=False, visible=True
    )
    results2 = create_results(batch2, fake_pathway)
    yield
    for result in results1:
        result.delete()
    batch1.delete()
    for result in results2:
        result.delete()
    batch2.delete()


@pytest.mark.django_db
def test_normal_view(api_client, fake_questionnaire):
    url = reverse("results", kwargs={"id": fake_questionnaire.id})
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.json()["bought"]["count"] == 3
    assert response.json()["not_bought_count"] == 3


@pytest.mark.django_db
def test_filter(api_client, fake_questionnaire):
    url = reverse("results", kwargs={"id": fake_questionnaire.id})
    response = api_client.get(f"{url}?feedback=1")

    assert response.status_code == 200
    assert response.json()["bought"]["count"] == 1
    assert response.json()["bought"]["results"][0]["name"] == "test1"
    # make sure not bought don't get filtered either
    assert response.json()["not_bought_count"] == 3


@pytest.mark.django_db
def test_filter_favorite(api_client, fake_questionnaire):
    url = reverse("results", kwargs={"id": fake_questionnaire.id})
    response = api_client.get(f"{url}?favorite=true")

    assert response.status_code == 200
    assert response.json()["bought"]["count"] == 1
    assert response.json()["bought"]["results"][0]["name"] == "test1"
    # make sure not bought don't get filtered either
    assert response.json()["not_bought_count"] == 3


@pytest.mark.django_db
def test_ordering(api_client, fake_questionnaire):
    url = reverse("results", kwargs={"id": fake_questionnaire.id})
    response = api_client.get(f"{url}?ordering=-feedback")

    assert response.status_code == 200
    results = response.json()["bought"]["results"]
    for index in range(0, len(results) - 1):
        assert results[index]["feedback"] >= results[index + 1]["feedback"]
