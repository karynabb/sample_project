import datetime
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from app.algorithm.models import Result
from app.game.exceptions import GameGenerationError
from app.game.models import Game, GameConfig
from app.game.services.game_options_generator_service import (
    GameOptionsGeneratorService,
)

logger = logging.getLogger(__name__)


class GameCreationService:

    @classmethod
    def create_game_with_error_retries(
        cls, game_config: GameConfig, date: datetime.date, override_game: bool = True
    ):
        attempt_number = 0

        option_last_used_in_game_threshold = (
            settings.OPTION_LAST_USED_IN_GAME_DAYS_THRESHOLD
        )
        while (
            attempt_number < settings.MAX_ATTEMPTS_TO_GENERATE_GAME
            and option_last_used_in_game_threshold > 0
        ):
            try:
                logger.info(
                    f"Attempt {attempt_number} to generate a game for date {date} started"
                )
                cls.create_game(
                    game_config, option_last_used_in_game_threshold, date, override_game
                )
                return
            except (ValidationError, IntegrityError) as e:
                attempt_number += 1
                logger.error(
                    f"Attempt {attempt_number} to generate a game for date {date} failed: {e}"
                )
                option_last_used_in_game_threshold -= (
                    settings.LAST_USED_IN_GAME_DATE_INCREMENT_DAYS
                )

        logger.error(f"Exceeded attempts number to generate a game for date {date}")
        raise GameGenerationError(
            f"Exceeded attempts number to generate a game for date {date}"
        )

    @staticmethod
    def create_game(
        game_config: GameConfig,
        option_last_used_in_game_threshold: int,
        date: datetime.date,
        override_game: bool,
    ):
        with transaction.atomic():
            try:
                existing_game = Game.objects.get_game_by_date(date)
                if existing_game:
                    if not override_game:
                        logger.error(
                            f"Game already exists for {existing_game.date}, "
                            f"override_game set to False skipping creation because {override_game=}"
                        )
                        return
                    else:
                        logger.error(
                            f"Game already exists for {date}, override_game set to True setting "
                            f"options {existing_game.options_id_list} to previous state"
                        )
                        GameOptionsGeneratorService.revert_options_to_previous_state(
                            existing_game.options_id_list
                        )
                options_id_list = GameOptionsGeneratorService.generate_options(
                    option_last_used_in_game_threshold,
                    game_config.number_of_words_lvl1,
                    game_config.number_of_words_lvl2,
                    date,
                )
                sorted_options_id_list = sorted(options_id_list)
                new_game, created = Game.objects.create_game(
                    date=date,
                    options_id_list=sorted_options_id_list,
                    game_config_id=game_config.id,
                )

                Result.objects.update_game_usage(sorted_options_id_list, date)
                logger.info(
                    f"New game for date {date} was generated with id {new_game.id}"
                )
            except IntegrityError as e:
                logger.error(f"Game duplication detected for the date {date}: {e}")
                raise e
