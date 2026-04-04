from django.urls import path
from . import views

app_name = "housing"

urlpatterns = [
    path("module/",                              views.ModuleSettingsView.as_view(),           name="module"),
    path("listings/",                            views.HousingListingsView.as_view(),          name="listings"),
    path("listings/<uuid:pk>/",                  views.HousingListingDetailView.as_view(),     name="listing-detail"),
    path("listings/<uuid:pk>/save/",             views.ToggleSaveHousingView.as_view(),        name="toggle-save"),
    path("uploads/",                             views.HousingUploadView.as_view(),            name="upload"),
    path("roommates/",                           views.RoommateProfilesView.as_view(),         name="roommates"),
    path("alerts/notifications/",                views.AlertNotificationsView.as_view(),       name="alert-notifications"),       # ← before <uuid:pk>
    path("alerts/notifications/<uuid:pk>/",      views.AlertNotificationDetailView.as_view(), name="alert-notification-detail"),  # ← before <uuid:pk>
    path("alerts/",                              views.AlertsView.as_view(),                   name="alerts"),
    path("alerts/<uuid:pk>/",                    views.AlertDetailView.as_view(),              name="alert-detail"),
    path("stats/",                               views.HousingStatsView.as_view(),             name="stats"),
]