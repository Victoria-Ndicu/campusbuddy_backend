from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    CreateAlertSerializer, CreateHousingListingSerializer,
    CreateRoommatePreferenceSerializer, CreateRoommateProfileSerializer,
    HousingListingSerializer, HousingModuleSettingsSerializer,
    RoommatePreferenceSerializer, RoommateProfileSerializer,
    UpdateHousingListingSerializer,
)


class HousingListingsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["max_rent", "min_bedrooms", "search"]}
        # tags can be multi-value: ?tags=apartment&tags=hostel
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
        # Attach compatibility score using the profile-to-profile scorer
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


class ModuleSettingsView(APIView):
    """Admin only. GET current state; POST {"enabled": true/false} to toggle."""
    def get(self, request):
        return Response(services.get_module_settings())

    def post(self, request):
        enabled = request.data.get("enabled")
        if not isinstance(enabled, bool):
            return Response({"error": {"code": "INVALID", "message": "'enabled' must be a boolean."}}, status=400)
        return Response(services.toggle_module(enabled, request.user))