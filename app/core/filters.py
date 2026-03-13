from django_filters import BooleanFilter, FilterSet, NumberFilter

from app.algorithm.models import Result
from app.core.models import Payment, PaymentStatus, PaymentType, Questionnaire


class QuestionnaireFilter(FilterSet):
    payed = BooleanFilter(method="filter_payed")

    def filter_payed(self, queryset, name, payed: bool):
        completed_initials = Payment.objects.filter(
            user=self.request.user,
            payment_type=PaymentType.INITIAL,
            status=PaymentStatus.COMPLETED,
        )
        paid_q_ids = completed_initials.values_list("questionnaire__id", flat=True)
        unpaid_questionnaires = Questionnaire.objects.exclude(id__in=paid_q_ids)
        if payed:
            return queryset.exclude(id__in=unpaid_questionnaires)
        return queryset.filter(id__in=unpaid_questionnaires)

    class Meta:
        model = Questionnaire
        fields = ["payed"]


class ResultFilter(FilterSet):
    feedback = NumberFilter(field_name="feedback", lookup_expr="exact")

    class Meta:
        model = Result
        fields = ["feedback", "favorite"]
