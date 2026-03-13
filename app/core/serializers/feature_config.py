from rest_framework import serializers


class FeatureConfigSerializer(serializers.Serializer):
    pricing_plan = serializers.SerializerMethodField()

    def get_pricing_plan(self, obj):
        return obj.pricing_plan
