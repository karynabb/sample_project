import logging
from typing import Type

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from app.core import tasks
from app.core.models import Payment, User
from app.core.utils import get_first_batch, get_is_pricing_plan_free, get_new_batch

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Payment)
def next_step_trigger(sender, instance, **kwargs):
    if not get_is_pricing_plan_free():
        try:
            obj = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:  # new object
            pass
        else:
            prev_status = obj.status != "completed"
            new_status = instance.status == "completed"
            if prev_status and new_status:
                other_payments = obj.questionnaire.payments.filter(status="completed")
                if not other_payments:
                    get_first_batch(instance.questionnaire)


@receiver(post_save, sender=Payment)
def bought_new_batch(sender, instance, **kwargs):
    if not get_is_pricing_plan_free():
        if instance.status == "completed" and instance.payment_type == "buy_more":
            get_new_batch(instance.questionnaire)


@receiver(post_save, sender=User, dispatch_uid="create-hubspot-contact")
def create_hubspot_contact(sender: Type[User], instance: User, **kwargs):
    tasks.create_hubspot_contact.delay(
        instance.email, instance.first_name, instance.last_name
    )
