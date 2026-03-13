from rest_framework import serializers

from app.expert.models import ResultReview


class ResultReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultReview
        fields = ["expert_feedback", "expert_like"]
