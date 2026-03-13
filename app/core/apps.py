import logging

import spacy
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.core"

    def ready(self):
        try:
            settings.LANGUAGE_MODELS["en_core_web_lg"] = spacy.load("en_core_web_lg")
        except IOError as e:
            logger.warning(str(e))
        __import__("app.core.signals")
