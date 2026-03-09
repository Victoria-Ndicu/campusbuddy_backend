"""
Authentication views — thin wrappers that validate input and delegate to services.
No business logic lives here.
"""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import AppError

from . import services
from .serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    OtpVerifySerializer,
    RefreshSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
)


class RegisterView(APIView):
    """POST /api/v1/auth/register"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        result = services.register_user(
            email=d["email"],
            password=d["password"],
            phone=d.get("phone", ""),
        )
        return Response(result, status=status.HTTP_201_CREATED)


class VerifyOtpView(APIView):
    """POST /api/v1/auth/verify-otp"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        result = services.verify_otp(email=d["email"], code=d["code"])
        return Response(result)


class LoginView(APIView):
    """POST /api/v1/auth/login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        result = services.login_user(email=d["email"], password=d["password"])
        return Response(result)


class RefreshView(APIView):
    """POST /api/v1/auth/refresh"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.refresh_tokens(serializer.validated_data["refresh"])
        return Response(result)


class ForgotPasswordView(APIView):
    """POST /api/v1/auth/forgot-password"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.forgot_password(serializer.validated_data["email"])
        return Response(result)


class ResetPasswordView(APIView):
    """POST /api/v1/auth/reset-password"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        result = services.reset_password(
            email=d["email"],
            code=d["code"],
            new_password=d["newPassword"],
        )
        return Response(result)


class LogoutView(APIView):
    """POST /api/v1/auth/logout"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.logout_user(serializer.validated_data["refresh"])
        return Response(result)


class MeView(APIView):
    """GET /api/v1/auth/me"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "isVerified": user.is_verified,
            "createdAt": user.created_at.isoformat(),
        })