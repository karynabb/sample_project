from rest_framework import serializers

from app.algorithm.models import Result
from app.game.models import Game


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ["id", "name", "offering_description", "rationale"]


class GameSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ["date", "options"]

    def get_options(self, obj):
        options = Result.objects.select_related("batch__questionnaire").filter(
            id__in=obj.options_id_list
        )
        return OptionSerializer(options, many=True).data


class GameDatesSerializer(serializers.Serializer):
    dates = serializers.ListField()
    start_date = serializers.DateTimeField(allow_null=True)
    end_date = serializers.DateTimeField(allow_null=True)
