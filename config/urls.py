from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from apps.housing.views import UserPreferencesView


def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)    

def root(request):
    return JsonResponse({
        "message": "CampusBuddy API is running",
        "health": "/health/",
        "api": "/api/v1/"
    })


urlpatterns = [
    # Root 
    path("", root),

    # Admin
    path("admin/", admin.site.urls),

    # Health
    path("health/", health_check, name="health"),

    # API v1
    path("api/v1/user/preferences/", UserPreferencesView.as_view(), name="user-preferences"),
    path("api/v1/auth/",        include("apps.authentication.urls", namespace="auth")),
    path("api/v1/profile/",     include("apps.profiles.urls",       namespace="profiles")),
    path("api/v1/market/",      include("apps.market.urls",         namespace="market")),
    path("api/v1/housing/",     include("apps.housing.urls",        namespace="housing")),
    path("api/v1/events/",      include("apps.events.urls",         namespace="events")),
    path("api/v1/study-buddy/", include("apps.study.urls",          namespace="study")),
]