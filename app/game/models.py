import logging

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel

from app.game.consts import NUMBER_OF_OPTIONS
from app.game.managers import GameManager
from app.game.validators import validate_options_id_list

logger = logging.getLogger(__name__)


class GameConfig(TimeStampedModel):
    number_of_words_lvl1 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="No. of complexity 1 names",
    )
    number_of_words_lvl2 = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="No. of complexity 2 names",
    )
    is_active = models.BooleanField(default=False)

    def clean(self):
        if self.number_of_words_lvl1 + self.number_of_words_lvl2 != NUMBER_OF_OPTIONS:
            raise ValidationError(
                f"Total number of words must be equal to {NUMBER_OF_OPTIONS}"
            )

    def save(self, *args, **kwargs):
        self.clean()
        if self.is_active:
            GameConfig.objects.filter(is_active=True).update(is_active=False)
        super(GameConfig, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("number_of_words_lvl1", "number_of_words_lvl2")


class Game(TimeStampedModel):
    objects: GameManager = GameManager()

    game_config = models.ForeignKey(GameConfig, on_delete=models.SET_NULL, null=True)
    options_id_list = ArrayField(
        models.IntegerField(),
        size=NUMBER_OF_OPTIONS,
        validators=[validate_options_id_list],
        unique=True,
    )
    date = models.DateField(unique=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
