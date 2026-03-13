from django.urls import path

from app.tracker import views

urlpatterns = [
    path(
        "tracker/events/questionnaire",
        views.CreateQuestionnaireEventView.as_view(),
        name="create_questionnaire_event",
    ),
]
