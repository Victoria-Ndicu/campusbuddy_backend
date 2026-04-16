"""EventBoard views — campus_id removed, date/month filters + reminder DELETE."""
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    BroadcastSerializer,
    CreateEventSerializer,
    DeleteReminderSerializer,
    EventSerializer,
    ReminderSerializer,
    RSVPSerializer,
    UpdateEventSerializer,
)


class EventsView(APIView):
    """
    GET  /api/v1/events/   → list published events (paginated)
    POST /api/v1/events/   → create & publish event

    GET query params (all optional):
      category   – academic | social | sports | career | other
      search     – title contains
      from_date  – events starting on/after YYYY-MM-DD
      date       – events whose start_at is on this exact date  (YYYY-MM-DD)
      month      – events whose start_at is in this month       (YYYY-MM)
    """

    def get(self, request):
        filters = {
            k: request.query_params.get(k)
            for k in ["category", "search", "from_date", "date", "month"]
        }
        qs = services.list_events(filters, request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)

        # Attach per-user flags (isSaved, isRsvped, userRsvp) to each event
        data = [services._serialize_event(event, request.user) for event in page]
        return paginator.get_paginated_response(data)

    def post(self, request):
        s = CreateEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            services.create_event(s.validated_data, request.user), status=201
        )


class EventDetailView(APIView):
    """
    GET    /api/v1/events/<id>/   → event detail + userRsvp + isSaved
    PATCH  /api/v1/events/<id>/   → update (organiser only)
    DELETE /api/v1/events/<id>/   → cancel  (organiser only)
    """

    def get(self, request, pk):
        return Response(services.get_event(str(pk), request.user))

    def patch(self, request, pk):
        s = UpdateEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            services.update_event(str(pk), s.validated_data, request.user)
        )

    def delete(self, request, pk):
        return Response(services.delete_event(str(pk), request.user))


class EventBannerUploadView(APIView):
    """
    POST /api/v1/events/uploads/banner/

    Accepts two content types:
      • multipart/form-data  — field name 'file'  (existing behaviour)
      • application/json     — body { "image": "data:<mime>;base64,<data>" }

    Returns { success: true, data: { bannerUrl: "https://..." } }
    """
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        # ── JSON / base64 path ────────────────────────────────────────
        if request.content_type and "application/json" in request.content_type:
            data_uri = request.data.get("image")
            if not data_uri:
                return Response(
                    {"error": {"code": "NO_IMAGE", "message": "No image provided."}},
                    status=400,
                )
            return Response(
                services.upload_banner_base64(data_uri, request.user), status=201
            )

        # ── Multipart / file path ─────────────────────────────────────
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
    POST   /api/v1/events/reminders/
           Body: { "event_id": "<uuid>", "remind_at": "<ISO datetime>" }
           → set or update a reminder

    DELETE /api/v1/events/reminders/
           Body: { "event_id": "<uuid>" }
           → remove the reminder for this user+event
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

    def delete(self, request):
        s = DeleteReminderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            services.delete_reminder(
                str(s.validated_data["event_id"]),
                request.user,
            )
        )


class EventSaveView(APIView):
    """
    POST   /api/v1/events/<id>/save/  → save event   (returns saved: true)
    DELETE /api/v1/events/<id>/save/  → unsave event  (returns saved: false)
    """

    def post(self, request, pk):
        return Response(services.toggle_save(str(pk), request.user))

    def delete(self, request, pk):
        return Response(services.toggle_save(str(pk), request.user))


class MyRSVPsView(APIView):
    """
    GET /api/v1/events/my-rsvps/
    Returns a paginated list of events the authenticated user has RSVPed to.
    Each event includes userRsvp, isRsvped, and isSaved fields.

    Optional query param:
      ?status=going|not_going|waitlist  — filter by RSVP status
    """

    def get(self, request):
        status_filter = request.query_params.get("status")
        qs = services.list_my_rsvps(request.user, rsvp_status_filter=status_filter)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        
        # ✅ FIXED: Use _serialize_event to get consistent data structure
        data = [services._serialize_event(event, request.user) for event in page]
        
        return paginator.get_paginated_response(data)


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