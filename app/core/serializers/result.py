from rest_framework import serializers

from app.algorithm.models import Result
from app.core.models.choices import QuestionnaireExpertReviewStatus
from app.expert.serializers import ResultReviewSerializer


class ResultSerializer(serializers.ModelSerializer):
    strategy = serializers.CharField(source="pathway.global_rationale")
    expert_review = ResultReviewSerializer(read_only=True)

    class Meta:
        model = Result
        fields = [
            "id",
            "name",
            "rationale",
            "feedback",
            "erroneous",
            "favorite",
            "strategy",
            "expert_review",
            "example_phrases",
            "batch_id",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        picks_shown = instance.batch.questionnaire.picks_shown
        if (
            instance.batch.questionnaire.common_expert_review_status
            == QuestionnaireExpertReviewStatus.COMPLETED.value
            or picks_shown
        ):
            representation["expert_review"] = ResultReviewSerializer(
                instance.expert_review
            ).data
        else:
            representation.pop("expert_review", None)
        return representation
