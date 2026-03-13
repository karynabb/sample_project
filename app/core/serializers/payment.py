from rest_framework import serializers

from app.core.enums import DonationSourceEnum
from app.core.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "questionnaire",
            "stripe_id",
            "checkout_url",
            "payment_type",
        ]


class UnauthenticatedPaymentSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()


class DonationRequestSerializer(serializers.Serializer):
    success_url = serializers.URLField()
    failure_url = serializers.URLField()
    donation_source = serializers.ChoiceField(
        choices=DonationSourceEnum.choices(),
        default=DonationSourceEnum.APP.value,
    )
