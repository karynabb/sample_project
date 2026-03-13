from __future__ import annotations

from typing import TypeVar

from django.db import models
from model_utils.managers import InheritanceManager

from app.algorithm.models import Pathway
from app.core.models import Questionnaire, User

M = TypeVar("M", bound=models.Model, covariant=True)


class BaseManager(models.Manager[M]):
    pass


class Event(models.Model):
    """Base class for events"""

    timestamp = models.DateTimeField()
    objects: InheritanceManager[Event] = InheritanceManager()

    @property
    def signature(self):
        return self.__class__.__name__


class QuestionnaireEvent(Event):
    objects: InheritanceManager[QuestionnaireEvent] = InheritanceManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    draft = models.IntegerField(default=0)


class NextButtonQuestionnaire(QuestionnaireEvent):
    objects = InheritanceManager["NextButtonQuestionnaire"]()
    action_name = "questionnaire_next"


class PreviousButtonQuestionnaire(QuestionnaireEvent):
    objects = InheritanceManager["PreviousButtonQuestionnaire"]()
    action_name = "questionnaire_prev"


class QueryLog(models.Model):
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE, related_name="+")
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="+"
    )
    query = models.TextField(default="")
    input_word = models.CharField(max_length=200)
    tokens_consumed = models.IntegerField(default=0)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
