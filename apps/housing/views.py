from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .models import HousingAlert, AlertNotification
from .serializers import (
    CreateAlertSerializer, CreateHousingListingSerializer,
    CreateRoommatePreferenceSerializer, CreateRoommateProfileSerializer,
    HousingListingSerializer, HousingModuleSettingsSerializer,
    RoommatePreferenceSerializer, RoommateProfileSerializer,
    UpdateHousingListingSerializer,
)


class HousingModuleView(APIView):
    """Admin only. GET current state; POST {"enabled": true/false} to toggle."""
    def get(self, request):
        return Response(services.get_module_settings())

    def post(self, request):
        enabled = request.data.get("enabled")
        if not isinstance(enabled, bool):
            return Response({"error": {"code": "INVALID", "message": "'enabled' must be a boolean."}}, status=400)
        return Response(services.toggle_module(enabled, request.user))


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
            return Response({"error": {"code": "NO_FILE", "message": "No file provided."}}, status=400)
        return Response(services.upload_image(file, request.user), status=201)


class RoommateProfilesView(APIView):
    def get(self, request):
        profiles = services.get_roommate_profiles(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(profiles, request)
        data = RoommateProfileSerializer(page, many=True).data
        try:
            my_profile = request.user.roommate_profile
            for item, profile in zip(data, page):
                item["compatibilityScore"] = services.compute_compatibility(my_profile, profile)
        except Exception:
            pass
        return paginator.get_paginated_response(data)

    def post(self, request):
        s = CreateRoommateProfileSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.upsert_roommate_profile(s.validated_data, request.user))


class RoommatePreferenceView(APIView):
    def get(self, request):
        return Response(services.get_roommate_preference(request.user))

    def post(self, request):
        s = CreateRoommatePreferenceSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.upsert_roommate_preference(s.validated_data, request.user))


class AlertsView(APIView):
    def get(self, request):
        qs = services.list_alerts(request.user)
        return Response({"success": True, "data": list(qs.values())})

    def post(self, request):
        s = CreateAlertSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_alert(s.validated_data, request.user), status=201)


class AlertDetailView(APIView):
    def delete(self, request, pk):
        return Response(services.delete_alert(str(pk), request.user))


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


class HousingStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import HousingListing
        return Response({
            "listings":    HousingListing.objects.filter(status="active").count(),
            "matches":     0,
            "near_campus": 0,
            "alerts":      HousingAlert.objects.filter(user=request.user, active=True).count(),
        })


# Alias kept for backwards compatibility with ModuleSettingsView name if used elsewhere
ModuleSettingsView = HousingModuleView