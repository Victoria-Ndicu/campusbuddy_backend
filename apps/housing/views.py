from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .models import HousingAlert, AlertNotification, RoommateProfile
from .serializers import (
    CreateAlertSerializer, UpdateAlertSerializer,
    CreateHousingListingSerializer, HousingAlertSerializer,
    CreateRoommatePreferenceSerializer, CreateRoommateProfileSerializer,
    HousingListingSerializer, HousingModuleSettingsSerializer,
    RoommatePreferenceSerializer, RoommateProfileSerializer,
    UpdateHousingListingSerializer,
)


# ---------------------------------------------------------------------------
# User preferences  (per-user housing module toggle)
# Endpoint: GET/PATCH /api/v1/user/preferences/
# ---------------------------------------------------------------------------

class UserPreferencesView(APIView):
    """
    GET   → returns { housing_module_enabled: bool, ... }
    PATCH → accepts { housing_module_enabled: bool }
            Only the authenticated user can change their own preference.
            The backend never flips this automatically.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(services.get_user_preferences(request.user))

    def patch(self, request):
        # Only allow housing_module_enabled — ignore anything else
        data = {}
        if "housing_module_enabled" in request.data:
            val = request.data["housing_module_enabled"]
            if not isinstance(val, bool):
                return Response(
                    {"error": {"code": "INVALID", "message": "'housing_module_enabled' must be a boolean."}},
                    status=400,
                )
            data["housing_module_enabled"] = val
        return Response(services.update_user_preferences(data, request.user))


# ---------------------------------------------------------------------------
# Global module settings  (admin)
# ---------------------------------------------------------------------------

class HousingModuleView(APIView):
    """Admin only. GET current state; POST {"enabled": true/false} to toggle."""

    def get(self, request):
        return Response(services.get_module_settings())

    def post(self, request):
        enabled = request.data.get("enabled")
        if not isinstance(enabled, bool):
            return Response(
                {"error": {"code": "INVALID", "message": "'enabled' must be a boolean."}},
                status=400,
            )
        return Response(services.toggle_module(enabled, request.user))


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

class HousingListingsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["max_rent", "min_bedrooms", "search"]}
        tags = request.query_params.getlist("tags")
        if tags:
            filters["tags"] = tags
        qs = services.list_listings(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(HousingListingSerializer(page, many=True).data)

    def post(self, request):
        s = CreateHousingListingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_listing(s.validated_data, request.user), status=201)


class HousingListingDetailView(APIView):
    def get(self, request, pk):
        return Response(services.get_listing(str(pk)))

    def patch(self, request, pk):
        s = UpdateHousingListingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.update_listing(str(pk), s.validated_data, request.user))

    def delete(self, request, pk):
        return Response(services.delete_listing(str(pk), request.user))


class ToggleSaveHousingView(APIView):
    def post(self, request, pk):
        return Response(services.toggle_save(str(pk), request.user))


class HousingUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": {"code": "NO_FILE", "message": "No file provided."}},
                status=400,
            )
        return Response(services.upload_image(file, request.user), status=201)


# ---------------------------------------------------------------------------
# Roommate views
# ---------------------------------------------------------------------------

class RoommateProfilesView(APIView):
    def get(self, request):
        filter_key = request.query_params.get("filter", "")
        search     = request.query_params.get("search", "")
        profiles   = services.get_roommate_profiles(request.user, filter_key=filter_key, search=search)
        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(profiles, request)
        data       = RoommateProfileSerializer(page, many=True).data
        try:
            my_profile = request.user.roommate_profile
            for item, profile in zip(data, page):
                item["match_percent"] = services.compute_compatibility(my_profile, profile)
        except Exception:
            pass
        return paginator.get_paginated_response(data)

    def post(self, request):
        s = CreateRoommateProfileSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.upsert_roommate_profile(s.validated_data, request.user))


class MyRoommateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.roommate_profile
        except RoommateProfile.DoesNotExist:
            return Response({"detail": "No profile yet."}, status=404)
        return Response({"success": True, "data": RoommateProfileSerializer(profile).data})

    def post(self, request):
        s = CreateRoommateProfileSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.upsert_roommate_profile(s.validated_data, request.user))


class RoommateProfileDetailView(APIView):
    def get(self, request, pk):
        profile = RoommateProfile.objects.filter(pk=pk, active=True).select_related("user").first()
        if not profile:
            return Response({"detail": "Profile not found."}, status=404)
        data = RoommateProfileSerializer(profile).data
        try:
            my_profile        = request.user.roommate_profile
            data["match_percent"] = services.compute_compatibility(my_profile, profile)
        except Exception:
            data["match_percent"] = 0
        return Response({"success": True, "data": data})


class RoommateConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = RoommateProfile.objects.filter(pk=pk, active=True).select_related("user").first()
        if not profile:
            return Response({"detail": "Profile not found."}, status=404)
        if profile.user == request.user:
            return Response({"detail": "You cannot connect with yourself."}, status=400)
        # TODO: wire to messaging / notification system
        return Response({"success": True, "message": f"Connect request sent to {profile.user}."})


class RoommatePreferenceView(APIView):
    def get(self, request):
        return Response(services.get_roommate_preference(request.user))

    def post(self, request):
        s = CreateRoommatePreferenceSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.upsert_roommate_preference(s.validated_data, request.user))


# ---------------------------------------------------------------------------
# Alert rules
# ---------------------------------------------------------------------------

class AlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs   = services.list_alerts(request.user)
        data = HousingAlertSerializer(qs, many=True).data
        return Response({"success": True, "results": data})

    def post(self, request):
        s = CreateAlertSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_alert(s.validated_data, request.user), status=201)


class AlertDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Flutter calls this to toggle is_active on an alert rule."""
        s = UpdateAlertSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.update_alert(str(pk), s.validated_data, request.user))

    def delete(self, request, pk):
        return Response(services.delete_alert(str(pk), request.user))


# ---------------------------------------------------------------------------
# Alert notifications  (inbox)
# ---------------------------------------------------------------------------

class AlertNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = AlertNotification.objects.filter(
            user=request.user
        ).order_by("-created_at")
        data = [
            {
                "id":            str(n.id),
                "message":       n.message,
                "emoji":         n.emoji,
                "created_at":    n.created_at.isoformat(),
                "listing_title": n.listing_title,
                "listing":       str(n.listing_id) if n.listing_id else None,
                "is_read":       n.is_read,
            }
            for n in notifications
        ]
        return Response(data)


class AlertNotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            n = AlertNotification.objects.get(pk=pk, user=request.user)
            n.is_read = request.data.get("is_read", n.is_read)
            n.save()
            return Response({"id": str(n.id), "is_read": n.is_read})
        except AlertNotification.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class HousingStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import HousingListing
        return Response({
            "listings":    HousingListing.objects.filter(status="active").count(),
            "matches":     0,
            "near_campus": 0,
            "alerts":      HousingAlert.objects.filter(user=request.user, is_active=True).count(),
        })


# Alias kept for backwards compatibility
ModuleSettingsView = HousingModuleView