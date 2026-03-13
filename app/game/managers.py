import datetime
import logging

from django.db import models
from django.db.models import Q, QuerySet
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class GameManager(models.Manager):
    def create_game(
        self, date: datetime.date, options_id_list: list[int], game_config_id: int
    ):
        return self.update_or_create(
            date=date,
            defaults={
                "options_id_list": options_id_list,
                "game_config_id": game_config_id,
            },
        )

    def get_game_by_date(self, date: datetime.date):
        return self.filter(date=date).first()

    def retrieve_games(
        self,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> QuerySet:
        filters = Q()
        if start_date:
            filters &= Q(date__gte=start_date)
        if end_date:
            filters &= Q(date__lte=end_date)

        queryset: QuerySet = self.filter(filters).all()
        valid_games_id_list = []
        for game in queryset:
            try:
                game.full_clean()
                valid_games_id_list.append(game.id)
            except ValidationError as e:
                logger.error(f"Removing game {game.id} from valid games list, {e}")
        return self.filter(id__in=valid_games_id_list)

    def get_latest_game_by_option_id(self, option_id: int):
        self.filter(options_id_list__contains=[option_id]).order_by("-date").first()
