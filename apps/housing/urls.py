from django.urls import path
from . import views

app_name = "housing"

urlpatterns = [
    # ── Admin module settings ───────────────────────────────────────────────
    path("module/",                              views.HousingModuleView.as_view(),               name="module"),

    # ── Listings ───────────────────────────────────────────────────────────
    path("listings/",                            views.HousingListingsView.as_view(),             name="listings"),
    path("listings/<uuid:pk>/",                  views.HousingListingDetailView.as_view(),        name="listing-detail"),
    path("listings/<uuid:pk>/save/",             views.ToggleSaveHousingView.as_view(),           name="toggle-save"),

    # ── Uploads ────────────────────────────────────────────────────────────
    path("uploads/",                             views.HousingUploadView.as_view(),               name="upload"),

    # ── Roommates ──────────────────────────────────────────────────────────
    # my-profile/ and <uuid>/connect/ MUST come before <uuid:pk>/
    path("roommates/",                           views.RoommateProfilesView.as_view(),            name="roommates"),
    path("roommates/my-profile/",                views.MyRoommateProfileView.as_view(),           name="roommate-my-profile"),
    path("roommates/<uuid:pk>/connect/",         views.RoommateConnectView.as_view(),             name="roommate-connect"),
    path("roommates/<uuid:pk>/",                 views.RoommateProfileDetailView.as_view(),       name="roommate-detail"),
    path("roommate-preference/",                 views.RoommatePreferenceView.as_view(),          name="roommate-preference"),

    # ── Alerts ─────────────────────────────────────────────────────────────
    # notifications/ MUST come before <uuid:pk>/
    path("alerts/notifications/",                views.AlertNotificationsView.as_view(),          name="alert-notifications"),
    path("alerts/notifications/<uuid:pk>/",      views.AlertNotificationDetailView.as_view(),     name="alert-notification-detail"),
    path("alerts/",                              views.AlertsView.as_view(),                      name="alerts"),
    path("alerts/<uuid:pk>/",                    views.AlertDetailView.as_view(),                 name="alert-detail"),

    # ── Stats ──────────────────────────────────────────────────────────────
    path("stats/",                               views.HousingStatsView.as_view(),                name="stats"),
]