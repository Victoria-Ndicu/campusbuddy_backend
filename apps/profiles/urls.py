from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("me/",                          views.ProfileView.as_view(),             name="me"),
    path("avatar/",                      views.AvatarView.as_view(),              name="avatar"),
    path("password/",                    views.PasswordView.as_view(),            name="password"),
    path("preferences/",                 views.PreferencesView.as_view(),         name="preferences"),
    path("device-token/",                views.DeviceTokenView.as_view(),         name="device-token"),
    path("feedback/",                    views.FeedbackView.as_view(),            name="feedback"),
    path("notifications/",               views.NotificationsView.as_view(),       name="notifications"),
    path("notifications/<uuid:pk>/read/", views.MarkNotificationReadView.as_view(), name="notification-read"),
]