from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse


@admin.action(description="Generate missing offering descriptions and rationales")
def generate_missing_offering_descriptions_rationales(modeladmin, request, queryset):
    return HttpResponseRedirect(reverse("admin:generate_missing_game_data"))


@admin.action(description="Generate games")
def generate_games_action(modeladmin, request, queryset):
    return HttpResponseRedirect(reverse("admin:generate_games"))
