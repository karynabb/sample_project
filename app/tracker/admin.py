from django.contrib import admin

from app.tracker import models


@admin.register(models.QuestionnaireEvent)
class QuestionnaireEventAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "draft", "action_type"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_subclasses()

    @staticmethod
    def action_type(instance):
        return instance.action_name


@admin.register(models.QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ["pathway", "duration", "tokens_consumed"]

    def duration(self, instance):
        return instance.end_time - instance.start_time
