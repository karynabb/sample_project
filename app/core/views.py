import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.openapi import IN_QUERY, TYPE_INTEGER, TYPE_STRING, Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param

from app.algorithm.models import Result
from app.core.clients.stripe_client.client import StripeClient
from app.core.clients.stripe_client.event_handlers import (
    EventHandler,
    GiftCardHandler,
)
from app.core.enums import DonationSourceEnum
from app.core.filters import QuestionnaireFilter, ResultFilter
from app.core.helpers import StandardResultsSetPagination
from app.core.models import (
    DraftQuestionnaire,
    FeatureConfig,
    Payment,
    PaymentStatus,
    PaymentType,
    Questionnaire,
)
from app.core.models.price import ProductPrice
from app.core.permissions import OwnerPermissions
from app.core.serializers import (
    DraftQuestionnaireSerializer,
    FeedbackSerializer,
    PaymentSerializer,
    QuestionnaireSerializer,
    ResultSerializer,
    UserSerializer,
)
from app.core.serializers.feature_config import FeatureConfigSerializer
from app.core.serializers.payment import (
    DonationRequestSerializer,
    UnauthenticatedPaymentSerializer,
)
from app.core.tasks import update_hubspot_client_to_opportunity
from app.core.typing import AnswerSchema, DraftSchema
from app.core.utils import get_first_batch, get_is_pricing_plan_free, get_new_batch
from app.expert.models import ExpertPlusReview
from app.expert.serializers import ExpertPlusReviewSerializer

logger = logging.getLogger(__name__)


class CreateQuestionnaireView(generics.CreateAPIView):
    serializer_class = QuestionnaireSerializer
    permission_classes = [IsAuthenticated]
    parameters = [
        f"{k}: type {v['type']}" for k, v in AnswerSchema.schema()["properties"].items()
    ]

    @swagger_auto_schema(
        manual_parameters=[
            Parameter(
                "Answers", IN_QUERY, description="\n".join(parameters), type=TYPE_STRING
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        return super().create(request, *args, **kwargs)


class CreateDraftQuestionnaireView(generics.CreateAPIView):
    serializer_class = DraftQuestionnaireSerializer
    permission_classes = [IsAuthenticated]
    parameters = [
        f"{name}: type {values['type']}"
        for name, values in DraftSchema.schema()["properties"].items()
    ]

    @swagger_auto_schema(
        manual_parameters=[
            Parameter(
                "Answers", IN_QUERY, description="\n".join(parameters), type=TYPE_STRING
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        return super().create(request, *args, **kwargs)


class QuestionnaireDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionnaireSerializer
    lookup_url_kwarg = "id"
    permission_classes = [IsAuthenticated, OwnerPermissions]
    queryset = Questionnaire.objects.all()


class DraftQuestionnaireDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DraftQuestionnaireSerializer
    lookup_url_kwarg = "id"
    permission_classes = [IsAuthenticated, OwnerPermissions]
    queryset = DraftQuestionnaire.objects.all()


class UpdateAndViewUserInfo(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class QuestionnaireListView(generics.ListAPIView):
    serializer_class = QuestionnaireSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_class = QuestionnaireFilter
    filter_backends = [OrderingFilter, DjangoFilterBackend]

    def get_queryset(self):
        return Questionnaire.objects.filter(user=self.request.user).order_by("-id")


class DraftListView(generics.ListAPIView):
    serializer_class = DraftQuestionnaireSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return DraftQuestionnaire.objects.filter(user=self.request.user).order_by(
            "-created"
        )


class CreatePayment(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, OwnerPermissions]
    queryset = Questionnaire.objects.all()
    lookup_field = "id"

    @swagger_auto_schema(
        responses={"201": "Returns Payment model instance"},
        manual_parameters=[
            Parameter(
                "questionnaire",
                IN_QUERY,
                "Id of a questionnaire",
                type=TYPE_INTEGER,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        self.kwargs[self.lookup_field] = request.data.get("questionnaire")
        questionnaire: Questionnaire = self.get_object()

        if questionnaire.has_completed_payment:
            return HttpResponse(
                status=400, content="Payment has already been created and completed"
            )

        redirect_url = f"{request.build_absolute_uri('/')}questionnaire/"
        session = StripeClient.create_checkout_session(redirect_url, questionnaire.id)
        data = {
            "questionnaire": questionnaire.id,
            "stripe_id": session["id"],
            "checkout_url": session["url"],
            "payment_type": "initial",
        }

        existing_initial_payment = questionnaire.initial_payment_in_progress
        if existing_initial_payment is not None:
            # Pricing plan might have changed so need to update the Stripe product id
            existing_initial_payment.stripe_id = session["id"]
            existing_initial_payment.checkout_url = session["url"]
            existing_initial_payment.save()
            serializer = PaymentSerializer(existing_initial_payment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = PaymentSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(("GET",))
@authentication_classes([])
@permission_classes([])
def get_gift_card_session(request: HttpRequest):
    batches_amount = request.GET.get("batches_amount", None)
    if batches_amount is not None:
        try:
            converted_batches_amount = int(batches_amount)
        except ValueError:
            batches_amount = None
    redirect_url = request.GET.get("redirect_url", None)
    if redirect_url is None or batches_amount is None:
        return Response(
            "Invalid GET parameters: expected string redirect_url and integer batches_amount",
            status=status.HTTP_400_BAD_REQUEST,
        )

    front_base_url = f"{request.build_absolute_uri('/')}"
    session = StripeClient.create_gift_card_session(
        front_base_url, redirect_url, converted_batches_amount
    )
    return Response(
        {"stripe_id": session["id"], "checkout_url": session["url"]},
        status=status.HTTP_200_OK,
    )


@api_view(("GET",))
@authentication_classes([])
@permission_classes([])
def get_email_with_promo_codes(request: HttpRequest):
    stripe_id = request.GET.get("stripe_id", None)
    if stripe_id is not None:
        try:
            session = StripeClient.retrieve_session(stripe_id)
        except ValueError:
            session = None
    else:
        return Response(
            {"message": "Failed to retrieve the Stripe session."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not session:
        return Response(
            {"message": "Failed to retrieve the Stripe session."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    gift_card_handler = GiftCardHandler()
    email_with_promo_codes = gift_card_handler._get_email(session)
    return Response(
        {"email_with_promo_codes": email_with_promo_codes},
        status=status.HTTP_200_OK,
    )


class BuyMore(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, OwnerPermissions]
    queryset = Questionnaire.objects.all()
    lookup_field = "id"

    @swagger_auto_schema(
        responses={"201": "Returns Payment model instance"},
        manual_parameters=[
            Parameter(
                "questionnaire",
                IN_QUERY,
                "Id of a questionnaire",
                type=TYPE_INTEGER,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        self.kwargs[self.lookup_field] = request.data.get("questionnaire")
        questionnaire: Questionnaire = self.get_object()
        is_pricing_plan_free = get_is_pricing_plan_free()
        if not questionnaire.has_available_batches:
            return HttpResponse(status=400, content="No more batches to buy")
        if not questionnaire.has_completed_payment and not is_pricing_plan_free:
            return HttpResponse(status=400, content="No initial payment")

        if is_pricing_plan_free:
            result = get_new_batch(questionnaire)
            return Response(
                {"message": "New batch is added to the user", **(result or {})},
                status=200,
            )
        else:
            redirect_url = f"{request.build_absolute_uri('/')}journey/"
            session = StripeClient.create_checkout_session(
                redirect_url, questionnaire.id
            )
            data = {
                "questionnaire": questionnaire.id,
                "stripe_id": session["id"],
                "checkout_url": session["url"],
                "payment_type": "buy_more",
            }
            serializer = PaymentSerializer(data=data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )


class PaymentInfo(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    lookup_url_kwarg = "id"
    permission_classes = [IsAuthenticated, OwnerPermissions]
    queryset = Payment.objects.all()


@csrf_exempt
def stripe_payment_webhook(request: HttpRequest, source: str | None = None):
    signature_header = request.headers.get("STRIPE_SIGNATURE")

    webhook_secret = (
        settings.STRIPE_SECONDARY_WEBHOOK_SECRET
        if source == DonationSourceEnum.SECONDARY.value.lower()
        else settings.STRIPE_WEBHOOK_SECRET
    )

    try:
        event = stripe.Webhook.construct_event(
            request.body, signature_header, webhook_secret
        )
    except ValueError:
        raise ValueError("Invalid payload from stripe")

    return EventHandler.handle_event(event)


class ResultsListView(generics.GenericAPIView):
    serializer_class = ResultSerializer
    filterset_class = ResultFilter
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"
    ordering_fields = ["feedback", "favorite", "erroneous", "name"]

    def get_queryset(self):
        ids_correct = Q(batch__questionnaire_id=self.kwargs[self.lookup_url_kwarg])
        user_permission = Q(batch__questionnaire__user=self.request.user)
        batch_visible = Q(batch__visible=True)
        return Result.objects.filter(ids_correct & user_permission & batch_visible)

    def get_not_rated_results_count(self, queryset):
        """Get not rated results from bought batches."""
        return queryset.filter(
            Q(feedback=0) & Q(erroneous=False) & Q(favorite=False)
        ).aggregate(count=Count("id"))

    def get(self, request, *args, **kwargs):
        if self.lookup_url_kwarg not in self.kwargs:
            return HttpResponse(status=400)

        all_results = self.get_queryset()
        not_bought = all_results.filter(batch__bought=False)
        bought = self.filter_queryset(all_results.filter(batch__bought=True))

        expert_plus_reviews = ExpertPlusReview.objects.filter(
            expert_batch_review__result_batch__questionnaire_id=self.kwargs[
                self.lookup_url_kwarg
            ]
        )
        expert_plus_review_serializer = ExpertPlusReviewSerializer(
            expert_plus_reviews, many=True
        )
        is_review_completed = (
            Questionnaire.objects.get(
                id=self.kwargs[self.lookup_url_kwarg]
            ).common_expert_review_status
            == "completed"
        )

        not_rated_results_count = self.get_not_rated_results_count(queryset=bought).get(
            "count", 0
        )
        bought_count = bought.count()
        serializer = self.get_serializer(bought, many=True)
        return Response(
            {
                "bought": {
                    "rated_results_count": bought_count - not_rated_results_count,
                    "not_rated_results_count": not_rated_results_count,
                    "count": bought_count,
                    "results": serializer.data,
                    "expert_plus_reviews": (
                        expert_plus_review_serializer.data
                        if is_review_completed
                        else []
                    ),
                },
                "not_bought_count": not_bought.count(),
                "batch_size": FeatureConfig.get_active_config().batch_size,
            }
        )


class PresentationListView(generics.ListAPIView):
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if self.lookup_url_kwarg not in self.kwargs:
            return HttpResponse(status=400)

        questionnaire_id = self.kwargs[self.lookup_url_kwarg]
        return Result.objects.filter(
            batch__questionnaire_id=questionnaire_id, batch__bought=True
        ).order_by("id")

    def sort_results(self, queryset):
        """Sort presentation results and put not rated items to the end of the presentation."""

        def custom_sort_key(result):
            """Custom key to sort results."""
            return (
                result.feedback == 0 and not result.erroneous and not result.favorite,
            )

        return sorted(queryset, key=custom_sort_key)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        sorted_queryset = self.sort_results(queryset=queryset)
        serializer = self.get_serializer(sorted_queryset, many=True)
        expert_plus_reviews = ExpertPlusReview.objects.filter(
            expert_batch_review__result_batch__questionnaire_id=self.kwargs[
                self.lookup_url_kwarg
            ]
        )
        expert_plus_review_serializer = ExpertPlusReviewSerializer(
            expert_plus_reviews, many=True
        )
        is_review_completed = (
            Questionnaire.objects.get(
                id=self.kwargs[self.lookup_url_kwarg]
            ).common_expert_review_status
            == "completed"
        )
        return Response(
            {
                "results": serializer.data,
                "expert_plus_reviews": (
                    expert_plus_review_serializer.data if is_review_completed else []
                ),
            }
        )


class FeedBackUpdateView(generics.UpdateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Result.objects.filter(batch__questionnaire__user=self.request.user)


class CompleteDraft(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, OwnerPermissions]
    lookup_url_kwarg = "id"
    queryset = DraftQuestionnaire.objects.all()
    serializer_class = QuestionnaireSerializer

    @swagger_auto_schema(responses={"201": "Created", "400": "Unable to complete"})
    def post(self, request, *args, **kwargs):
        draft = self.get_object()
        if draft.ready_to_complete:
            with transaction.atomic():
                new_questionnaire = Questionnaire.objects.create(
                    name=draft.name,
                    user=draft.user,
                    answers=draft.answers,
                    parent=draft.parent,
                    expert_review_payed=False,
                    expert_plus_payed=False,
                )
                draft.delete()
            update_hubspot_client_to_opportunity.delay(draft.user.id)
            if get_is_pricing_plan_free():
                get_first_batch(new_questionnaire)
            serializer = self.get_serializer(new_questionnaire)
            return Response(serializer.data)
        else:
            return HttpResponse(status=400)


class CreateChild(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, OwnerPermissions]
    lookup_url_kwarg = "id"
    queryset = Questionnaire.objects.all()
    serializer_class = DraftQuestionnaireSerializer

    def post(self, request, *args, **kwargs):
        questionnaire = self.get_object()
        last_edited = request.data.get("last_edited_question", 0)
        new_child_draft = questionnaire.create_child(last_edited)
        serializer = self.get_serializer(new_child_draft)
        return Response(serializer.data)


class ContinueView(generics.ListAPIView):
    """
    Custom view to present unpaid questionnaires and drafts in one place
    Questionnaires are shown first, then drafts.
    Pagination is implemented through query param: page
    """

    PAGE_SIZE = 10

    def generate_prev_page(self, current_page):
        current_url = self.request.build_absolute_uri()
        if "https" not in current_url and "http" in current_url:
            current_url = current_url.replace("http", "https")
        if current_page and current_page > 1:
            return replace_query_param(current_url, "page", current_page - 1)
        return ""

    def generate_next_page(self, element_count, current_page, page_size):
        current_url = self.request.build_absolute_uri()
        if "https" not in current_url and "http" in current_url:
            current_url = current_url.replace("http", "https")
        if current_page:
            if current_page * page_size < element_count:
                return replace_query_param(current_url, "page", current_page + 1)
        elif element_count > page_size:
            return replace_query_param(current_url, "page", 2)
        return ""

    def get_queryset(self):
        """Returns a list; not a django queryset, mypy can sue me"""
        drafts = DraftQuestionnaire.objects.filter(user=self.request.user)
        completed_initials = Payment.objects.filter(
            user=self.request.user,
            payment_type=PaymentType.INITIAL,
            status=PaymentStatus.COMPLETED,
        )
        paid_q_ids = completed_initials.values_list("questionnaire__id", flat=True)
        if get_is_pricing_plan_free():
            unpaid_questionnaires = Questionnaire.objects.none()
        else:
            unpaid_questionnaires = Questionnaire.objects.filter(
                user=self.request.user
            ).exclude(id__in=paid_q_ids)
        draft_response = DraftQuestionnaireSerializer(drafts, many=True)
        for draft_dict in draft_response.data:
            draft_dict["type"] = "draft"
        questionnaire_response = QuestionnaireSerializer(
            unpaid_questionnaires, many=True
        )
        for q_dict in questionnaire_response.data:
            q_dict["type"] = "questionnaire"
        return [*questionnaire_response.data, *draft_response.data]

    def list(self, request, *args, **kwargs):
        limit = int(request.GET.get("limit", 0)) or self.PAGE_SIZE
        response_list = self.get_queryset()
        result_count = len(response_list)
        if page := int(request.query_params.get("page", 1)):
            start = (page - 1) * limit
            response_list = response_list[start : start + limit]

        return Response(
            {
                "count": len(response_list),
                "next": self.generate_next_page(result_count, page, limit),
                "previous": self.generate_prev_page(page),
                "results": response_list,
            }
        )


class FeatureConfigRetrieveView(generics.RetrieveAPIView):
    serializer_class = FeatureConfigSerializer

    def get_object(self):
        feature_config = FeatureConfig.get_active_config()
        return feature_config


class MakeDonation(generics.GenericAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = DonationRequestSerializer

    @swagger_auto_schema(
        request_body=DonationRequestSerializer,
        responses={"200": "Returns Unauthenticated Payment model instance"},
    )
    def post(self, request, *args, **kwargs):
        input_data = self.get_serializer(data=request.data)
        input_data.is_valid(raise_exception=True)

        success_url = input_data.validated_data.get("success_url")
        failure_url = input_data.validated_data.get("failure_url")
        source = input_data.validated_data.get("donation_source")

        try:
            donation_price = ProductPrice.objects.get(
                name__icontains=f"Donation {source}"
            )
        except ProductPrice.DoesNotExist:
            raise Http404(f"Price Donation {source} does not exist")

        session = StripeClient.create_donation_session(
            success_url, failure_url, donation_price.stripe_price_id, source
        )
        payment_data = {
            "checkout_url": session["url"],
        }
        serializer = UnauthenticatedPaymentSerializer(data=payment_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
