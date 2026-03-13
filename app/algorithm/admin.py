from django.contrib import admin
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html

from app.algorithm import models


@admin.register(models.NegativeDataset)
class NegativeDatasetAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "word",
    ]


@admin.register(models.Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "candidates_per_batch", "cascade_level", "active"]

    def for_datasets(self, instance):
        return ",".join(instance.datasets.values_list("code", flat=True))


class InlineResult(admin.TabularInline):
    model = models.Result


class EmptyOfferingDescriptionResultFilter(admin.SimpleListFilter):
    title = "Offering Description"
    parameter_name = "is_empty_offering_description"

    def lookups(self, request, model_admin):
        return (
            ("1", "Empty"),
            ("0", "Not empty"),
        )

    def queryset(self, request, queryset):
        val = self.value()
        empty_q = Q(batch__questionnaire__offering_description__isnull=True) | Q(
            batch__questionnaire__offering_description__exact=""
        )
        if val == "1":
            return queryset.filter(empty_q)
        if val == "0":
            return queryset.exclude(empty_q)
        return queryset


@admin.register(models.Result)
class ResultAdmin(admin.ModelAdmin):
    readonly_fields = [
        "questionnaire",
        "was_used_in_game_date",
        "number_was_used_in_game",
    ]

    list_display = [
        "id",
        "name",
        "batch",
        "bought",
        "feedback",
        "erroneous",
        "favorite",
        "pathway",
        "game_complexity_level",
        "questionnaire",
        "was_used_in_game_date",
        "number_was_used_in_game",
    ]
    list_filter = [
        "favorite",
        "erroneous",
        "pathway",
        "game_complexity_level",
        ("rationale", admin.EmptyFieldListFilter),
        ("was_used_in_game_date", admin.EmptyFieldListFilter),
        EmptyOfferingDescriptionResultFilter,
    ]
    list_editable = ["game_complexity_level"]
    search_fields = ("name",)

    def bought(self, instance):
        return instance.batch.bought

    def questionnaire(self, instance):
        questionnaire = instance.batch.questionnaire
        questionnaire_admin_url = reverse(
            "admin:{}_{}_change".format(
                questionnaire._meta.app_label, questionnaire._meta.model_name
            ),
            args=[questionnaire.id],
        )
        return format_html(
            '<a href="{}">{}</a>', questionnaire_admin_url, questionnaire.name
        )


@admin.register(models.NameCandidate)
class NameCandidateAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "questionnaire", "pathway", "scoring"]
    search_fields = (
        "questionnaire__name",
        "name",
    )
    list_filter = ["pathway"]


@admin.register(models.ResultBatch)
class BatchAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_questionnaire_link",
        "get_user_link",
        "bought",
        "result_count",
        "visible",
        "expert_review_required",
    ]
    inlines = [InlineResult]
    search_fields = ("questionnaire__name",)

    def get_questionnaire_link(self, instance):
        questionnaire = instance.questionnaire
        questionnaire_admin_url = reverse(
            "admin:{}_{}_change".format(
                questionnaire._meta.app_label, questionnaire._meta.model_name
            ),
            args=[questionnaire.id],
        )
        return format_html(
            '<a href="{}">{}</a>', questionnaire_admin_url, questionnaire.name
        )

    def get_user_link(self, instance):
        user = instance.questionnaire.user
        user_admin_url = reverse(
            "admin:{}_{}_change".format(user._meta.app_label, user._meta.model_name),
            args=[user.id],
        )
        return format_html('<a href="{}">{}</a>', user_admin_url, user.email)

    get_user_link.short_description = "User"  # type: ignore
    get_questionnaire_link.short_description = "Questionnaire"  # type: ignore

    def result_count(self, instance):
        return instance.results.count()


@admin.register(models.LMMCache)
class CacheAdmin(admin.ModelAdmin):
    list_display = ["id", "pathway", "questionnaire"]
