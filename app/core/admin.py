from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from app.algorithm.tasks import generate_name_candidates
from app.core import models


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    def get_list_display(self, request):
        base = super().get_list_display(request)
        return *base, "date_joined"


@admin.register(models.Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "user", "offering_description", "created"]
    list_filter = [("offering_description", admin.EmptyFieldListFilter)]
    actions = ["create_child", "execute_generation_flow"]
    search_fields = ("name",)

    def create_child(self, request, queryset):
        for item in queryset:
            item.create_child()

    def execute_generation_flow(self, request, queryset):
        for item in queryset:
            generate_name_candidates.delay(item.id, True)


@admin.register(models.DraftQuestionnaire)
class DraftQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "last_edited_question", "created"]


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "questionnaire", "status", "stripe_id"]
    search_fields = ("questionnaire__name", "user__email", "user__username")
    list_filter = ["status"]


@admin.register(models.price.ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "stripe_price_id"]


@admin.register(models.BatchPrice)
class PriceAdmin(admin.ModelAdmin):
    list_display = ["id", "stripe_price_id", "batch_number", "pricing_plan"]


@admin.register(models.PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "internal_name"]

    def internal_name(self, obj: models.PricingPlan):
        return obj.name


@admin.register(models.FeatureConfig)
class FeatureConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "version", "active", "values"]
