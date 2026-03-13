from django.http import HttpResponse
from drf_yasg.openapi import IN_QUERY, TYPE_INTEGER, Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.core.clients.stripe_client.client import StripeClient
from app.core.models.price import ProductPrice
from app.core.models.questionnaire import Questionnaire
from app.core.permissions import OwnerPermissions
from app.core.serializers import PaymentSerializer
from app.core.utils import get_is_pricing_plan_free


class BuyExpertInTheLoop(generics.CreateAPIView):
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

        product_prices = ProductPrice.objects.filter(name__icontains="Expert").values(
            "name", "stripe_price_id"
        )
        expert_review_price = next(
            (
                p["stripe_price_id"]
                for p in product_prices
                if "Expert Review" in p["name"]
            ),
            None,
        )
        expert_plus_price = next(
            (
                p["stripe_price_id"]
                for p in product_prices
                if "Expert Plus" in p["name"]
            ),
            None,
        )

        is_expert_plus = request.data.get("is_expert_plus", False)

        if questionnaire.has_completed_payment:
            if is_expert_plus and (
                questionnaire.expert_plus_payed
                or questionnaire.has_completed_experts_payment
                or questionnaire.has_completed_expert_plus_payment
            ):
                return HttpResponse(
                    status=400, content="You have already paid for the expert plus"
                )
            elif not is_expert_plus and (
                questionnaire.expert_review_payed
                or questionnaire.has_completed_expert_review_payment
                or questionnaire.has_completed_experts_payment
            ):
                return HttpResponse(
                    status=400, content="You have already paid for the expert review"
                )
        elif not get_is_pricing_plan_free():
            return HttpResponse(status=400, content="No initial payment")

        redirect_url = f"{request.build_absolute_uri('/')}journey/"
        session, payment_type = StripeClient.create_expert_session(
            redirect_url,
            questionnaire.id,
            expert_review_price,
            expert_plus_price,
            is_expert_plus,
            questionnaire.expert_review_payed,
        )

        payment_data = {
            "questionnaire": questionnaire.id,
            "stripe_id": session["id"],
            "checkout_url": session["url"],
            "payment_type": payment_type,
        }

        serializer = PaymentSerializer(data=payment_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
