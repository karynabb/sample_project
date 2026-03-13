import logging
from datetime import date

from django.core.exceptions import ValidationError

from app.algorithm.models import Result
from app.core.models.choices import ResultsGameComplexityLevel

logger = logging.getLogger(__name__)


class GameOptionsGeneratorService:
    @classmethod
    def generate_options(
        cls,
        last_used_threshold: int,
        number_of_words_lvl1: int,
        number_of_words_lvl2: int,
        game_date: date,
    ):
        used_questionnaires_id_list: list[int] = []
        options_id_list_lvl1 = cls._generate_options_for_level(
            number_of_words_lvl1,
            ResultsGameComplexityLevel.LOW,
            last_used_threshold,
            used_questionnaires_id_list,
            game_date,
        )
        options_id_list_lvl2 = cls._generate_options_for_level(
            number_of_words_lvl2,
            ResultsGameComplexityLevel.MEDIUM,
            last_used_threshold,
            used_questionnaires_id_list,
            game_date,
        )
        options_id_list = options_id_list_lvl1 + options_id_list_lvl2
        return options_id_list

    @staticmethod
    def revert_options_to_previous_state(options_id_list: list[int]):
        for option_id in options_id_list:
            try:
                option = Result.objects.get(id=option_id)
                option.revert_game_usage()
            except Result.DoesNotExist:
                logger.error(f"Result {option_id} doesn't exist")

    @classmethod
    def _generate_options_for_level(
        cls,
        number_of_options: int,
        complexity_level: ResultsGameComplexityLevel,
        last_used_threshold: int,
        used_questionnaires_id_list: list[int],
        game_date: date,
    ):
        options_level_id_list = []
        for _ in range(number_of_options):
            option = cls._generate_option(
                complexity_level,
                last_used_threshold,
                used_questionnaires_id_list,
                game_date,
            )
            options_level_id_list.append(option.id)
            used_questionnaires_id_list.append(option.batch.questionnaire.id)
        return options_level_id_list

    @staticmethod
    def _generate_option(
        complexity_level: ResultsGameComplexityLevel,
        last_used_threshold: int,
        used_questionnaires_id_list: list[int],
        game_date: date,
    ):
        option = Result.objects.get_game_option(
            complexity_level,
            used_questionnaires_id_list,
            last_used_threshold,
            game_date,
        )
        if option is None:
            message = (
                f"Insufficient results to generate options "
                f"for complexity level {complexity_level.name}."
            )
            logger.error(message)
            raise ValidationError(message)
        else:
            logger.error(
                f"Found option {option.__dict__} offering description "
                f"{option.offering_description} with used_questionnaires_id_list"
                f" {used_questionnaires_id_list} and complexity_level {complexity_level}"
            )
        return option
