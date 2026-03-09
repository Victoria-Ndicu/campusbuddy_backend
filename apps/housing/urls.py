from django.urls import path
from . import views

app_name = "housing"

urlpatterns = [
    path("listings/",                  views.HousingListingsView.as_view(),      name="listings"),
    path("listings/<uuid:pk>/",        views.HousingListingDetailView.as_view(), name="listing-detail"),
    path("listings/<uuid:pk>/save/",   views.ToggleSaveHousingView.as_view(),    name="toggle-save"),
    path("uploads/",                   views.HousingUploadView.as_view(),        name="upload"),
    path("roommates/",                 views.RoommateProfilesView.as_view(),     name="roommates"),
    path("alerts/",                    views.AlertsView.as_view(),               name="alerts"),
    path("alerts/<uuid:pk>/",          views.AlertDetailView.as_view(),          name="alert-detail"),
]