from rest_framework import serializers

from app.tracker.models import (
    NextButtonQuestionnaire,
    PreviousButtonQuestionnaire,
    QuestionnaireEvent,
)


class QuestionnaireEventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionnaireEvent
        fields = ["user", "draft", "timestamp"]


class NextButtonQuestionnaireSerializer(QuestionnaireEventsSerializer):
    class Meta:
        model = NextButtonQuestionnaire
        fields = ["user", "draft", "timestamp"]


class PreviousButtonQuestionnaireSerializer(QuestionnaireEventsSerializer):
    class Meta:
        model = PreviousButtonQuestionnaire
        fields = ["user", "draft", "timestamp"]
