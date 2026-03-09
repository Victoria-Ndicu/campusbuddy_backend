from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .models import Notification
from .serializers import (
    DeleteAccountSerializer,
    DeviceTokenSerializer,
    FeedbackSerializer,
    NotificationSerializer,
    UpdatePasswordSerializer,
    UpdatePreferencesSerializer,
    UpdateProfileSerializer,
)


class ProfileView(APIView):
    """GET /profile/me/   PATCH /profile/me/"""

    def get(self, request):
        return Response(services.get_profile(request.user))

    def patch(self, request):
        serializer = UpdateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.update_profile(request.user, serializer.validated_data))

    def delete(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = request.META.get("REMOTE_ADDR")
        return Response(services.delete_account(request.user, serializer.validated_data["password"], ip))


class AvatarView(APIView):
    """POST /profile/avatar/"""
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("avatar")
        if not file:
            return Response({"error": {"code": "NO_FILE", "message": "No file uploaded."}}, status=400)
        return Response(services.upload_avatar(request.user, file))


class PasswordView(APIView):
    """PATCH /profile/password/"""

    def patch(self, request):
        serializer = UpdatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        return Response(services.change_password(request.user, d["currentPassword"], d["newPassword"]))


class PreferencesView(APIView):
    """PATCH /profile/preferences/"""

    def patch(self, request):
        serializer = UpdatePreferencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.update_preferences(request.user, serializer.validated_data))


class DeviceTokenView(APIView):
    """POST /profile/device-token/"""

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        return Response(services.register_device_token(request.user, d["token"], d["platform"]), status=201)


class FeedbackView(APIView):
    """POST /profile/feedback/"""

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        return Response(services.submit_feedback(request.user, d["message"], d.get("category", "other")), status=201)


class NotificationsView(APIView):
    """GET /profile/notifications/"""

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MarkNotificationReadView(APIView):
    """PATCH /profile/notifications/<id>/read/"""

    def patch(self, request, pk):
        updated = Notification.objects.filter(pk=pk, user=request.user).update(read=True)
        if not updated:
            return Response({"error": {"code": "NOT_FOUND", "message": "Notification not found."}}, status=404)
        return Response({"success": True})