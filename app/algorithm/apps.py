import json

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def load_default_pathways(sender, **kwargs):
    from algorithm_library.interfaces.configuration import PathwayConfig

    from app.algorithm.models import Pathway

    config_file = PathwayConfig().pathways_config
    with open(config_file, "r") as _file:
        config = json.load(_file)
        for pw_code, information in config.items():
            try:
                Pathway.objects.get(code=pw_code)
            except Pathway.DoesNotExist:
                Pathway.objects.create(
                    code=pw_code,
                    global_rationale=information["pathway_global_rationale"],
                )


class AlgorithmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.algorithm"

    def ready(self):
        post_migrate.connect(load_default_pathways, sender=self)
