"""EventBoard views — campus_id removed."""
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    BroadcastSerializer,
    CreateEventSerializer,
    EventSerializer,
    ReminderSerializer,
    RSVPSerializer,
    UpdateEventSerializer,
)


class EventsView(APIView):
    """
    GET  /api/v1/events/   → list published events
    POST /api/v1/events/   → create & publish event
    """

    def get(self, request):
        # campus_id filter removed
        filters = {
            k: request.query_params.get(k)
            for k in ["category", "search", "from_date"]
        }
        qs       = services.list_events(filters, request.user)
        paginator = StandardPagination()
        page     = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(EventSerializer(page, many=True).data)

    def post(self, request):
        s = CreateEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_event(s.validated_data, request.user), status=201)


class EventDetailView(APIView):
    """
    GET    /api/v1/events/<id>/   → event detail + userRsvp
    PATCH  /api/v1/events/<id>/   → update (organiser only)
    DELETE /api/v1/events/<id>/   → cancel  (organiser only)
    """

    def get(self, request, pk):
        return Response(services.get_event(str(pk), request.user))

    def patch(self, request, pk):
        s = UpdateEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.update_event(str(pk), s.validated_data, request.user))

    def delete(self, request, pk):
        return Response(services.delete_event(str(pk), request.user))


class EventBannerUploadView(APIView):
    """
    POST /api/v1/events/uploads/banner/
    Accepts multipart/form-data with field 'file'.
    Returns { success: true, data: { bannerUrl: "https://..." } }

    The Flutter client uses this URL as banner_url in the event payload.
    If this endpoint fails, Flutter falls back to embedding the base64
    data URI directly — the Event.banner_url TextField handles both.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": {"code": "NO_FILE", "message": "No file provided."}},
                status=400,
            )
        return Response(services.upload_banner(file, request.user), status=201)


class EventRSVPView(APIView):
    """
    POST /api/v1/events/<id>/rsvp/
    Body: { "status": "going" | "not_going" }
    """

    def post(self, request, pk):
        s = RSVPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            services.rsvp(str(pk), s.validated_data["status"], request.user)
        )


class EventReminderView(APIView):
    """
    POST /api/v1/events/reminders/
    Body: { "event_id": "<uuid>", "remind_at": "<ISO datetime>" }
    """

    def post(self, request):
        s = ReminderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            services.set_reminder(
                str(s.validated_data["event_id"]),
                s.validated_data["remind_at"],
                request.user,
            )
        )


class EventSaveView(APIView):
    """POST /api/v1/events/<id>/save/  → toggle saved state"""

    def post(self, request, pk):
        return Response(services.toggle_save(str(pk), request.user))


class EventBroadcastView(APIView):
    """
    POST /api/v1/events/<id>/broadcast/
    Body: { "message": "..." }
    Organiser only — sends push notification to all 'going' attendees.
    """

    def post(self, request, pk):
        s = BroadcastSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            services.broadcast_update(
                str(pk), s.validated_data["message"], request.user
            )
        )