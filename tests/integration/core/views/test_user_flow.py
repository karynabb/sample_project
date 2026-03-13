import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_edit_user_name(api_client, fake_user):
    url = reverse("user_management")
    response = api_client.patch(url, data={"first_name": "test_updated"})
    assert response.status_code == 200

    fake_user.refresh_from_db()
    assert fake_user.first_name == "test_updated"
