from django.urls import path
from . import views

app_name = "housing"

urlpatterns = [
    # ── Module settings ────────────────────────────────────────────────────
    path("module/",                              views.HousingModuleView.as_view(),               name="module"),

    # ── Listings ───────────────────────────────────────────────────────────
    path("listings/",                            views.HousingListingsView.as_view(),             name="listings"),
    path("listings/<uuid:pk>/",                  views.HousingListingDetailView.as_view(),        name="listing-detail"),
    path("listings/<uuid:pk>/save/",             views.ToggleSaveHousingView.as_view(),           name="toggle-save"),

    # ── Uploads ────────────────────────────────────────────────────────────
    path("uploads/",                             views.HousingUploadView.as_view(),               name="upload"),

    # ── Roommates ──────────────────────────────────────────────────────────
    # IMPORTANT: my-profile/ and <uuid>/connect/ must come BEFORE <uuid:pk>/
    # Django matches top-to-bottom; "my-profile" would be parsed as a UUID
    # and fail (returning 404) if the detail route appears first.
    path("roommates/",                           views.RoommateProfilesView.as_view(),            name="roommates"),
    path("roommates/my-profile/",                views.MyRoommateProfileView.as_view(),           name="roommate-my-profile"),
    path("roommates/<uuid:pk>/connect/",         views.RoommateConnectView.as_view(),             name="roommate-connect"),
    path("roommates/<uuid:pk>/",                 views.RoommateProfileDetailView.as_view(),       name="roommate-detail"),
    path("roommate-preference/",                 views.RoommatePreferenceView.as_view(),          name="roommate-preference"),

    # ── Alerts ─────────────────────────────────────────────────────────────
    # IMPORTANT: notifications/ must come BEFORE <uuid:pk>/ for the same reason
    path("alerts/notifications/",                views.AlertNotificationsView.as_view(),          name="alert-notifications"),
    path("alerts/notifications/<uuid:pk>/",      views.AlertNotificationDetailView.as_view(),     name="alert-notification-detail"),
    path("alerts/",                              views.AlertsView.as_view(),                      name="alerts"),
    path("alerts/<uuid:pk>/",                    views.AlertDetailView.as_view(),                 name="alert-detail"),

    # ── Stats ──────────────────────────────────────────────────────────────
    path("stats/",                               views.HousingStatsView.as_view(),                name="stats"),
]