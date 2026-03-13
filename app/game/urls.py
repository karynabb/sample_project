from django.urls import path

from app.game import views

urlpatterns = [
    path(
        "game/dates/",
        views.RetrieveAvailableGameDatesView.as_view(),
        name="game_dates",
    ),
    path(
        "game/<path:date>/",
        views.RetrieveGameView.as_view(),
        name="questionnaire_detail",
    ),
]
