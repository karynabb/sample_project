import typing

from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

from app.core.urls import urlpatterns as core_patterns
from app.expert.urls import urlpatterns as expert_patterns
from app.game.urls import urlpatterns as game_patterns
from app.tracker.urls import urlpatterns as tracker_patterns

from .views import healthy

URL = typing.Union[URLPattern, URLResolver]
URLList = typing.List[URL]

swagger_view = get_schema_view(
    openapi.Info(
        title="App API",
        default_version="v1",
        description="Overview of App API",
        terms_of_service="",
        contact=openapi.Contact(email="dev@example.com"),
        license=openapi.License(name="CC BY-ND"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns: URLList = [
    path("healthy/", healthy),
]

api_urls: URLList = [
    path(
        "", swagger_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"
    ),
    *core_patterns,
    *tracker_patterns,
    *expert_patterns,
    *game_patterns,
]

admin_urls: URLList = [
    path("", admin.site.urls),
]

if settings.INCLUDE_ADMIN_URLS:
    urlpatterns = [
        path("", include(urlpatterns)),
        path(settings.ADMIN_URLS_PATH, include(admin_urls)),
    ]

if settings.INCLUDE_API_URLS:
    urlpatterns = [
        path("", include(urlpatterns)),
        path(settings.API_URLS_PATH, include(api_urls)),
    ]
