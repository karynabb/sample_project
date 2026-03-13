from django.db import models

from .choices import PaymentStatus, PaymentType


class Payment(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="payments")
    stripe_id = models.CharField(max_length=100, null=True, blank=True)
    questionnaire = models.ForeignKey(
        "Questionnaire", on_delete=models.CASCADE, related_name="payments"
    )
    status = models.CharField(
        choices=PaymentStatus.choices, max_length=15, default=PaymentStatus.OPEN.value
    )
    checkout_url = models.URLField(max_length=400)
    payment_type = models.CharField(choices=PaymentType.choices, max_length=25)
