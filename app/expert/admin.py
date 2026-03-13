from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, Select
from django.urls import reverse
from django.utils.html import format_html

from app.algorithm.models import NameCandidate, Questionnaire
from app.expert import models
from app.expert.models import ResultReview


class CustomModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return format_html(
            f'<option title="{obj.rationale}" value="{obj.pk}">{obj.name}</option>'
        )


class ExpertPlusReviewForm(forms.ModelForm):
    suggested_name_class_b = CustomModelChoiceField(
        queryset=NameCandidate.objects.none(),
        required=False,
        label="Suggested Name from Name Candidates",
        widget=Select(
            attrs={"style": "width: 180px; overflow: hidden; text-overflow: ellipsis;"}
        ),
    )

    class Meta:
        model = models.ExpertPlusReview
        fields = ["suggested_name", "name_rationale", "expert_feedback"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["suggested_name"].widget.attrs["readonly"] = True
        self.fields["suggested_name"].widget.attrs["style"] = "width: 100px;"
        self.fields["name_rationale"].widget.attrs["style"] = "width: 400px;"
        self.fields["expert_feedback"].widget.attrs["style"] = "width: 400px;"

        if self.instance.pk and self.instance.expert_batch_review_id:
            questionnaire = self.instance.expert_batch_review.result_batch.questionnaire
            self.fields["suggested_name_class_b"].queryset = (
                NameCandidate.objects.filter(questionnaire=questionnaire)
            )

    def clean(self):
        cleaned_data = super().clean()
        suggested_name_class_b = cleaned_data.get("suggested_name_class_b")
        suggested_name = cleaned_data.get("suggested_name")
        name_rationale = cleaned_data.get("name_rationale")

        if suggested_name_class_b:
            suggested_name = suggested_name_class_b.name
            name_rationale = suggested_name_class_b.rationale

        cleaned_data["suggested_name"] = suggested_name
        cleaned_data["name_rationale"] = name_rationale

        return cleaned_data


class ExpertPlusReviewInline(admin.TabularInline):
    model = models.ExpertPlusReview
    form = ExpertPlusReviewForm
    extra = 0

    @staticmethod
    def has_add_permission(request, obj=None):
        return False


class ResultReviewForm(forms.ModelForm):
    class Meta:
        model = models.ResultReview
        fields = ["result", "expert_feedback", "expert_like"]


class ResultReviewInline(admin.TabularInline):
    model = models.ResultReview
    form = ResultReviewForm
    extra = 0

    fields = (
        "result_name",
        "rationale",
        "expert_feedback",
        "expert_like",
    )
    readonly_fields = ("result_name", "rationale")

    @staticmethod
    def result_name(instance):
        return format_html("<b>{}</b>", instance.result.name)

    @staticmethod
    def rationale(instance):
        return format_html(
            """
                <textarea style="
                width: 450px;
                height: 140px;
                border: 1px solid grey;
                border-radius: 5px;
                padding: 2px;
                ">{}</textarea>
            """,
            instance.result.rationale,
        )

    @staticmethod
    def has_add_permission(request, obj=None):
        return False


@admin.register(models.ExpertBatchReview)
class ExpertBatchReviewAdmin(admin.ModelAdmin):
    change_form_template = "admin/expert/expertplusreview/change_form.html"

    list_display = [
        "id",
        "questionnaire",
        "batch",
        "expert",
        "review_completed",
        "date_started",
        "result_batch",
    ]
    search_fields = ("expert__email",)
    list_filter = ["review_completed"]

    inlines = [ResultReviewInline, ExpertPlusReviewInline]

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            expert_batch_review = self.get_object(request, object_id)
            if expert_batch_review:
                related_questionnaire = Questionnaire.objects.filter(
                    result_batches=expert_batch_review.result_batch
                ).first()
                extra_context["related_questionnaire"] = related_questionnaire
        return super().changeform_view(request, object_id, form_url, extra_context)

    @staticmethod
    def questionnaire(instance):
        questionnaire = instance.result_batch.questionnaire
        questionnaire_admin_url = reverse(
            "admin:{}_{}_change".format(
                questionnaire._meta.app_label, questionnaire._meta.model_name
            ),
            args=[questionnaire.id],
        )
        return format_html(
            '<a href="{}">{}</a>', questionnaire_admin_url, questionnaire.name
        )

    @staticmethod
    def batch(instance):
        batch = instance.result_batch
        batch_admin_url = reverse(
            "admin:{}_{}_change".format(batch._meta.app_label, batch._meta.model_name),
            args=[batch.id],
        )
        return format_html('<a href="{}">{}</a>', batch_admin_url, batch.id)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "result_batch":
            queryset = models.ResultBatch.objects.filter(
                expert_review_required=models.ExpertReviewStatus.REQUIRED.value
            )

            expert_batch_review_id = request.resolver_match.kwargs.get("object_id")
            if expert_batch_review_id:
                current_instance = models.ExpertBatchReview.objects.filter(
                    pk=expert_batch_review_id
                ).first()
                if current_instance and current_instance.result_batch:
                    queryset |= models.ResultBatch.objects.filter(
                        pk=current_instance.result_batch.pk
                    )

            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            batch_results = obj.result_batch.results.all()
            for result in batch_results:
                models.ResultReview.objects.get_or_create(
                    result=result,
                    expert_batch_review=obj,
                )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance

        try:
            if obj.review_completed:
                self.validate_reviews(obj)
        except ValidationError as e:
            obj.review_completed = False
            obj.save()
            messages.error(request, e.message)

    def validate_reviews(self, obj):
        reviews = ResultReview.objects.filter(expert_batch_review=obj)
        self.validate_expert_feedback(reviews)
        self.validate_expert_plus_reviews(obj)

    def validate_expert_feedback(self, reviews):
        expert_feedbacks_count = 0
        for review in reviews:
            if review.expert_like and not review.expert_feedback:
                self.raise_validation_error(
                    "Feedback is required when expert likes the result. Review not completed."
                )
            elif not review.expert_like and review.expert_feedback:
                self.raise_validation_error(
                    "Feedback is not required when expert doesn't like the result. "
                    "Review not completed."
                )
            elif review.expert_feedback:
                expert_feedbacks_count += 1
        if expert_feedbacks_count < 3:
            self.raise_validation_error(
                "At least 3 results should be reviewed. Review not completed."
            )

    def validate_expert_plus_reviews(self, obj):
        expert_plus_reviews = models.ExpertPlusReview.objects.filter(
            expert_batch_review=obj
        )
        for expert_plus_review in expert_plus_reviews:
            if (
                expert_plus_review.suggested_name
                and not expert_plus_review.expert_feedback
            ):
                self.raise_validation_error(
                    "Feedback is required when expert suggests a name. Review not completed."
                )
            elif not expert_plus_review.suggested_name:
                self.raise_validation_error(
                    "Suggested name is required. Review not completed."
                )

    @staticmethod
    def raise_validation_error(message):
        raise ValidationError(message)
