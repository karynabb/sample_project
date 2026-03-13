from pydantic.errors import DictError
from rest_framework import serializers

from app.core.models import DraftQuestionnaire
from app.core.typing import DraftSchema
from app.core.utils import check_negative_dataset


class DraftQuestionnaireSerializer(serializers.ModelSerializer):
    user_has_payments = serializers.SerializerMethodField()

    def is_valid(self, *args, **kwargs):
        draft_keys = DraftSchema.schema()["properties"].keys()
        if any(key not in draft_keys for key in self.initial_data["answers"]):
            raise serializers.ValidationError("Unknown names of answers provided.")
        error_words = check_negative_dataset(self.initial_data["answers"])
        if error_words:
            raise serializers.ValidationError({"errors": error_words})
        try:
            DraftSchema.validate(self.initial_data["answers"])
        except DictError as errors:
            raise serializers.ValidationError(errors)
        super().is_valid(*args, **kwargs)

    @staticmethod
    def get_user_has_payments(obj):
        """
        Check if there are any payments associated with the user.
        """
        return obj.user.payments.exists()

    class Meta:
        model = DraftQuestionnaire
        fields = [
            "id",
            "user",
            "answers",
            "created",
            "modified",
            "name",
            "parent",
            "last_edited_question",
            "user_has_payments",
        ]
        read_only_fields = ["created", "modified", "parent", "user_has_payments"]
