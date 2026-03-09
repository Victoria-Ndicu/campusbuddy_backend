from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("",                          views.EventsView.as_view(),           name="list"),
    path("<uuid:pk>/",                views.EventDetailView.as_view(),      name="detail"),
    path("uploads/banner/",           views.EventBannerUploadView.as_view(), name="upload-banner"),
    path("<uuid:pk>/rsvp/",           views.EventRSVPView.as_view(),        name="rsvp"),
    path("reminders/",                views.EventReminderView.as_view(),    name="reminder"),
    path("<uuid:pk>/save/",           views.EventSaveView.as_view(),        name="save"),
    path("<uuid:pk>/broadcast/",      views.EventBroadcastView.as_view(),   name="broadcast"),
]