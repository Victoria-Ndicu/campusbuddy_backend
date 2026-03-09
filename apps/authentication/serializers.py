"""
Authentication serializers.
Input validation is handled here; business logic lives in services.py.
"""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class RegisterSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    phone    = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_password(self, value):
        validate_password(value)
        return value


class OtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code  = serializers.CharField(min_length=4, max_length=4)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email       = serializers.EmailField()
    code        = serializers.CharField(min_length=4, max_length=4)
    newPassword = serializers.CharField(min_length=8)

    def validate_newPassword(self, value):
        validate_password(value)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserBriefSerializer(serializers.ModelSerializer):
    """Minimal user payload included in token responses."""

    class Meta:
        model = User
        fields = ["id", "email", "role"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds extra user data to the JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        return token