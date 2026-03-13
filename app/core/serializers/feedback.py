from rest_framework import serializers

from app.algorithm.models import Result


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ["feedback", "erroneous", "favorite"]
