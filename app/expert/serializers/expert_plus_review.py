from rest_framework import serializers

from app.expert.models import ExpertPlusReview


class ExpertPlusReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertPlusReview
        fields = ["id", "suggested_name", "name_rationale", "expert_feedback"]
