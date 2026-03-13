from django.db.models import Q
from pydantic.errors import DictError
from rest_framework import serializers

from app.algorithm.models import Result, ResultBatch
from app.core.models import Questionnaire
from app.core.typing import AnswerSchema
from app.core.utils import check_negative_dataset


class QuestionnaireSerializer(serializers.ModelSerializer):
    has_results = serializers.SerializerMethodField()
    seen_results = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    user_has_payments = serializers.SerializerMethodField()

    def is_valid(self, *args, **kwargs):
        answer_keys = AnswerSchema.schema()["properties"].keys()
        if any(key not in answer_keys for key in self.initial_data["answers"]):
            raise serializers.ValidationError("Unknown names of answers provided.")
        error_words = check_negative_dataset(self.initial_data["answers"])
        if error_words:
            raise serializers.ValidationError({"errors": error_words})
        try:
            AnswerSchema.validate(self.initial_data["answers"])
        except DictError as errors:
            raise serializers.ValidationError(errors)
        super().is_valid(*args, **kwargs)

    @staticmethod
    def get_has_results(obj) -> bool:
        return ResultBatch.objects.filter(bought=True, questionnaire=obj).exists()

    @staticmethod
    def get_seen_results(obj) -> bool:
        batch_ids = ResultBatch.objects.filter(
            questionnaire=obj, bought=True
        ).values_list("id")
        return (
            Result.objects.filter(batch__in=batch_ids)
            .filter(Q(feedback__gt=0) | Q(erroneous=True) | Q(favorite=True))
            .exists()
        )

    @staticmethod
    def get_related(obj):
        child = Questionnaire.objects.filter(parent=obj)
        siblings = obj.siblings
        related = child.union(siblings)
        return [{"id": r.id, "name": r.name} for r in related]

    @staticmethod
    def get_parent_name(obj):
        if not obj.parent:
            return None

        return obj.parent.name

    @staticmethod
    def get_user_has_payments(obj):
        """
        Check if there are any payments associated with the user.
        """
        return obj.user.payments.exists()

    class Meta:
        model = Questionnaire
        fields = [
            "id",
            "user",
            "answers",
            "name",
            "parent",
            "parent_name",
            "created",
            "modified",
            "has_results",
            "seen_results",
            "failed",
            "related",
            "expert_review_payed",
            "expert_plus_payed",
            "common_expert_review_status",
            "user_has_payments",
        ]
        read_only_fields = ["parent", "created", "modified", "user_has_payments"]
