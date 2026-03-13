from django.apps import AppConfig


class ExpertConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.expert"

    def ready(self):
        __import__("app.expert.signals")
