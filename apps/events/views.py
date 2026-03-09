from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    BroadcastSerializer, CreateEventSerializer, EventSerializer,
    ReminderSerializer, RSVPSerializer, UpdateEventSerializer,
)


class EventsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["campus_id", "category", "search", "from_date"]}
        qs = services.list_events(filters, request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(EventSerializer(page, many=True).data)

    def post(self, request):
        s = CreateEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_event(s.validated_data, request.user), status=201)


class EventDetailView(APIView):
    def get(self, request, pk):
        return Response(services.get_event(str(pk), request.user))

    def patch(self, request, pk):
        s = UpdateEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.update_event(str(pk), s.validated_data, request.user))

    def delete(self, request, pk):
        return Response(services.delete_event(str(pk), request.user))


class EventBannerUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": {"code": "NO_FILE", "message": "No file provided."}}, status=400)
        return Response(services.upload_banner(file, request.user), status=201)


class EventRSVPView(APIView):
    def post(self, request, pk):
        s = RSVPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.rsvp(str(pk), s.validated_data["status"], request.user))


class EventReminderView(APIView):
    def post(self, request):
        s = ReminderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.set_reminder(
            str(s.validated_data["event_id"]), s.validated_data["remind_at"], request.user
        ))


class EventSaveView(APIView):
    def post(self, request, pk):
        return Response(services.toggle_save(str(pk), request.user))


class EventBroadcastView(APIView):
    def post(self, request, pk):
        s = BroadcastSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.broadcast_update(str(pk), s.validated_data["message"], request.user))