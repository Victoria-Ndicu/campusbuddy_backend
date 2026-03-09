from django.urls import path
from . import views

app_name = "auth"

urlpatterns = [
    path("register/",        views.RegisterView.as_view(),       name="register"),
    path("verify-otp/",      views.VerifyOtpView.as_view(),      name="verify-otp"),
    path("login/",           views.LoginView.as_view(),          name="login"),
    path("refresh/",         views.RefreshView.as_view(),        name="refresh"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/",  views.ResetPasswordView.as_view(),  name="reset-password"),
    path("logout/",          views.LogoutView.as_view(),         name="logout"),
    path("me/",              views.MeView.as_view(),             name="me"),
]