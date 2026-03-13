from django.db import models
from django.utils.translation import gettext_lazy as _


class PricingPlanName(models.TextChoices):
    A = "A", _("Pricing plan A (140, 110, 85, 55)")
    B = "B", _("Pricing plan B (75, 65, 55, 45)")
    FREE = "FREE", _("Pricing plan FREE")


class PaymentStatus(models.TextChoices):
    OPEN = "open", _("Open")
    CANCELLED = "cancelled", _("Cancelled")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")


class PaymentType(models.TextChoices):
    INITIAL = "initial", _("Initial")
    BUY_MORE = "buy_more", _("Buy more")
    EXPERT_IN_THE_LOOP = "expert_in_the_loop", _("Expert in the loop")
    EXPERT_PLUS = "expert_plus", _("Expert plus")
    EXPERTS = "experts", _("Experts")


class ExpertReviewStatus(models.TextChoices):
    NEW = "new", _("New")
    REQUIRED = "required", _("Required")
    PENDING = "pending", _("Pending")
    DONE = "done", _("Done")


class QuestionnaireExpertReviewStatus(models.TextChoices):
    REQUESTED = "requested", _("Requested")
    PENDING = "pending", _("Pending")
    COMPLETED = "completed", _("Completed")
    NOT_PAYED = "not_payed", _("Not payed")


class ResultsGameComplexityLevel(models.IntegerChoices):
    UNAVAILABLE = 0, _("Unavailable")
    LOW = 1, _("Low")
    MEDIUM = 2, _("Medium")
