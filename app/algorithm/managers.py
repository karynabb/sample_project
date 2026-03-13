from datetime import date, timedelta

from django.db import models
from django.db.models import F, Q

from app.core.models.choices import ResultsGameComplexityLevel


class ResultManager(models.Manager):
    def get_game_option(
        self,
        complexity_level: ResultsGameComplexityLevel,
        used_questionnaire_id_list: list[int],
        last_used_threshold: int,
        game_date: date,
    ):
        return (
            self.select_related("batch__questionnaire")
            .filter(
                Q(batch__questionnaire__offering_description__isnull=False)
                & ~Q(batch__questionnaire__offering_description=""),
                rationale__isnull=False,
                game_complexity_level=complexity_level.value,
            )
            .filter(
                Q(was_used_in_game_date__isnull=True)
                | Q(
                    was_used_in_game_date__lt=game_date
                    - timedelta(days=last_used_threshold)
                )
            )
            .exclude(batch__questionnaire__id__in=used_questionnaire_id_list)
            .order_by("number_was_used_in_game", "?")
            .first()
        )

    def update_game_usage(self, id_list: list, was_used_in_game_date: date):
        self.filter(id__in=id_list).update(
            was_used_in_game_date=was_used_in_game_date,
            number_was_used_in_game=F("number_was_used_in_game") + 1,
        )
