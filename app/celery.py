import os

from celery import Celery
from celery.schedules import crontab

"""Set default Celery configs"""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

app = Celery("app")

app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.beat_schedule = {
    "send_reminder_email_periodically": {
        "task": "schedule_sendgrid_send_reminder_email",
        "schedule": crontab(hour=8, minute=0),
    },
    "generate_games_periodically": {
        "task": "schedule_generate_games",
        "schedule": crontab(minute=0, hour=12, day_of_week=4),
    },
}

app.conf.timezone = "UTC"
app.autodiscover_tasks()
