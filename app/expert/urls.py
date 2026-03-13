from django.urls import path

from app.expert import views

urlpatterns = [
    path(
        "expert/buy",
        views.BuyExpertInTheLoop.as_view(),
        name="expert_buy",
    ),
]
