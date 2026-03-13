from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Manager

from app.core.models.questionnaire import DraftQuestionnaire, Questionnaire


class User(AbstractUser):
    middle_name = models.CharField(max_length=150, blank=True)
    reminder_email_sent = models.BooleanField(default=False)

    questionnaires: "Manager[Questionnaire]"
    drafts: "Manager[DraftQuestionnaire]"

    @property
    def full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"

    def __str__(self):
        return self.email
