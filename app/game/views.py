from django.contrib import messages
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import FormView
from drf_yasg.openapi import FORMAT_DATE, IN_QUERY, TYPE_STRING, Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from app.game.forms import (
    GamesGenerationForm,
    OfferingDescriptionsRationalesGenerationForm,
)
from app.game.models import Game
from app.game.serializers import GameDatesSerializer, GameSerializer
from app.game.tasks import (
    bulk_generate_rationale_offering_description,
    generate_games,
)
from app.game.utils import convert_str_to_date


class OfferingDescriptionsRationalesGenerationView(FormView):
    template_name = "admin/offering_descriptions_rationales_generation_form.html"
    form_class = OfferingDescriptionsRationalesGenerationForm
    success_url = reverse_lazy("admin:index")

    def form_valid(self, form):
        limit = form.cleaned_data["limit"]
        bulk_generate_rationale_offering_description.delay(limit)
        messages.success(
            self.request,
            "Generation of offering descriptions and rationales has started!",
        )
        return super().form_valid(form)


class GamesGenerationView(FormView):
    template_name = "admin/games_generation_form.html"
    form_class = GamesGenerationForm
    success_url = reverse_lazy("admin:index")

    def form_valid(self, form):
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        generate_games.delay(start_date, end_date)
        messages.success(
            self.request,
            "Generation of the games has started!",
        )
        return super().form_valid(form)


class RetrieveGameView(generics.RetrieveAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = GameSerializer

    def get_object(self, **kwargs):
        date = self.kwargs.get("date")
        try:
            game = Game.objects.get(date=date)
            game.full_clean()
            return game
        except Game.DoesNotExist:
            raise Http404(f"Game for a date {date} does not exist")


class RetrieveAvailableGameDatesView(GenericAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = GameDatesSerializer

    @swagger_auto_schema(
        responses={"200": "Returns available games dates"},
        manual_parameters=[
            (
                Parameter(
                    "start_date",
                    IN_QUERY,
                    "Start date of a range",
                    type=TYPE_STRING,
                    format=FORMAT_DATE,
                )
            ),
            (
                Parameter(
                    "end_date",
                    IN_QUERY,
                    "End date of a range",
                    type=TYPE_STRING,
                    format=FORMAT_DATE,
                )
            ),
        ],
    )
    def _get_query_params(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        start_date_formatted = convert_str_to_date(start_date) if start_date else None
        end_date_formatted = convert_str_to_date(end_date) if end_date else None
        return start_date_formatted, end_date_formatted

    def get(self, request, *args, **kwargs):
        start_date, end_date = self._get_query_params(request)
        available_games = Game.objects.retrieve_games(start_date, end_date)
        available_games_dates = available_games.values_list("date", flat=True)

        serializer = self.get_serializer(
            data={
                "dates": available_games_dates,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
