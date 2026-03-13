from django.contrib import admin
from django.urls import path
from django.utils.safestring import mark_safe

from app.algorithm.models import Result
from app.game import models
from app.game.actions import (
    generate_games_action,
    generate_missing_offering_descriptions_rationales,
)
from app.game.services.game_options_generator_service import (
    GameOptionsGeneratorService,
)
from app.game.views import (
    GamesGenerationView,
    OfferingDescriptionsRationalesGenerationView,
)


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ["created", "modified"]


@admin.register(models.GameConfig)
class GameConfigAdmin(BaseAdmin):
    list_display = [
        "id",
        "number_of_words_lvl1",
        "number_of_words_lvl2",
        "is_active",
        "created",
        "modified",
    ]

    actions = [generate_missing_offering_descriptions_rationales, generate_games_action]

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "generate-missing-game-data/",
                self.admin_site.admin_view(
                    OfferingDescriptionsRationalesGenerationView.as_view()
                ),
                name="generate_missing_game_data",
            ),
            path(
                "generate-games/",
                self.admin_site.admin_view(GamesGenerationView.as_view()),
                name="generate_games",
            ),
        ]
        return custom_urls + urls


@admin.register(models.Game)
class GameAdmin(BaseAdmin):
    list_display = ["id", "options_names", "created", "modified", "date"]
    readonly_fields = ["game_config", "options_detailed_view", "date"]

    def options_detailed_view(self, obj):
        if not obj.options_id_list:
            return "No options"

        options = Result.objects.select_related("batch__questionnaire").filter(
            id__in=obj.options_id_list
        )
        table_rows = "".join(
            f"<tr><td>{option.name}</td><td>{option.offering_description}"
            f"</td><td>{option.rationale}</td></tr>"
            for option in options
        )
        table_html = f"""
                <table style="border-collapse: collapse; width: 100%;">
                    <thead>
                        <tr>
                            <th style="border: 1px solid #ddd; padding: 8px;">Name</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">Description</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">Rationale</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                """
        return mark_safe(table_html)

    def options_names(self, obj):
        if not obj.options_id_list:
            return "No options"

        results = Result.objects.filter(id__in=obj.options_id_list)
        names = [result.name for result in results]

        return ", ".join(names)

    def delete_queryset(self, request, queryset):
        options_id_list = []
        for game in queryset:
            options_id_list.extend(game.options_id_list)
        GameOptionsGeneratorService.revert_options_to_previous_state(options_id_list)
        super().delete_queryset(request, queryset)
