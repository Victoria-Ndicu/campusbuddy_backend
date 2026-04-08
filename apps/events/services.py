"""EventBoard service layer — campus_id removed, base64 banner support."""
import base64
import uuid
from rest_framework import status
from core.exceptions import AppError
from core.services.storage_service import upload_file, validate_image
from .models import Event, EventReminder, EventRSVP, EventSaved
from .serializers import EventSerializer


# ─────────────────────────────────────────────────────────────
#  LIST
# ─────────────────────────────────────────────────────────────
def list_events(filters: dict, user):
    """
    GET /api/v1/events/
    Filters: category, search, from_date
    campus_id filter removed.
    """
    qs = Event.objects.filter(status="published")

    if filters.get("category"):
        qs = qs.filter(category=filters["category"])
    if filters.get("search"):
        qs = qs.filter(title__icontains=filters["search"])
    if filters.get("from_date"):
        qs = qs.filter(start_at__gte=filters["from_date"])

    return qs


# ─────────────────────────────────────────────────────────────
#  MY RSVPs
# ─────────────────────────────────────────────────────────────
def list_my_rsvps(user, rsvp_status_filter: str | None = None):
    """
    GET /api/v1/events/my-rsvps/
    Returns a queryset of Events the user has RSVPed to, annotated
    with the user's rsvp_status.  Optionally filtered by ?status=.
    """
    from django.db.models import CharField, Value
    from django.db.models.functions import Coalesce

    rsvp_qs = EventRSVP.objects.filter(user=user)
    if rsvp_status_filter:
        rsvp_qs = rsvp_qs.filter(rsvp_status=rsvp_status_filter)

    event_ids = rsvp_qs.values_list("event_id", flat=True)

    # Annotate each event with the user's rsvp_status via a subquery
    from django.db.models import OuterRef, Subquery
    user_rsvp_subquery = (
        EventRSVP.objects
        .filter(event=OuterRef("pk"), user=user)
        .values("rsvp_status")[:1]
    )

    qs = (
        Event.objects
        .filter(pk__in=event_ids)
        .annotate(user_rsvp_status=Subquery(user_rsvp_subquery, output_field=CharField()))
        .order_by("start_at")
    )
    return qs


# ─────────────────────────────────────────────────────────────
#  GET
# ─────────────────────────────────────────────────────────────
def get_event(event_id: str, user) -> dict:
    """
    GET /api/v1/events/<id>/
    Returns event data plus the current user's RSVP status.
    """
    event = _get_or_404(event_id)
    data  = EventSerializer(event).data
    rsvp  = EventRSVP.objects.filter(event=event, user=user).first()
    data["userRsvp"] = rsvp.rsvp_status if rsvp else None
    return {"success": True, "data": data}


# ─────────────────────────────────────────────────────────────
#  CREATE
# ─────────────────────────────────────────────────────────────
def create_event(data: dict, user) -> dict:
    """
    POST /api/v1/events/
    Creates and immediately publishes an event.
    banner_url may be a CDN URL or a base64 data URI.
    """
    clean = {k: v for k, v in data.items() if v is not None and v != ""}
    event = Event.objects.create(organiser=user, **clean)
    return {"success": True, "data": EventSerializer(event).data}


# ─────────────────────────────────────────────────────────────
#  UPDATE
# ─────────────────────────────────────────────────────────────
def update_event(event_id: str, data: dict, user) -> dict:
    event = _get_or_404(event_id)
    _assert_organiser(event, user)
    for field, value in data.items():
        setattr(event, field, value)
    event.save()
    return {"success": True, "data": EventSerializer(event).data}


# ─────────────────────────────────────────────────────────────
#  DELETE (soft — sets status = cancelled)
# ─────────────────────────────────────────────────────────────
def delete_event(event_id: str, user) -> dict:
    event = _get_or_404(event_id)
    _assert_organiser(event, user)
    event.status = "cancelled"
    event.save(update_fields=["status"])
    return {"success": True, "message": "Event cancelled."}


# ─────────────────────────────────────────────────────────────
#  BANNER UPLOAD
#
#  POST /api/v1/events/uploads/banner/
#
#  Accepts a multipart file.  Validates, uploads to cloud storage,
#  and returns the CDN URL.
#
#  The Flutter client falls back to storing the base64 data URI
#  directly as banner_url if this endpoint is unavailable.
#  The Event.banner_url field is TextField (no max_length) so both
#  short CDN URLs and long base64 strings are stored safely.
# ─────────────────────────────────────────────────────────────
def upload_banner(file, user) -> dict:
    validate_image(file, max_size_mb=20.0)
    url = upload_file(file, folder="events/banners", user_id=str(user.id))
    return {"success": True, "data": {"bannerUrl": url}}


def upload_banner_base64(data_uri: str, user) -> dict:
    """
    Alternative: accepts a base64 data URI, decodes it, uploads to storage,
    and returns a real CDN URL.

    Usage (optional — call from a separate view if you want to
    convert stored base64 URIs to real CDN URLs later):

        result = upload_banner_base64(event.banner_url, request.user)
        event.banner_url = result["data"]["bannerUrl"]
        event.save(update_fields=["banner_url"])
    """
    if not data_uri or not data_uri.startswith("data:"):
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_DATA_URI", "Expected a base64 data URI.")

    try:
        header, encoded = data_uri.split(",", 1)
        # header e.g. "data:image/jpeg;base64"
        mime = header.split(":")[1].split(";")[0]  # "image/jpeg"
        ext  = mime.split("/")[1]                  # "jpeg"
        image_bytes = base64.b64decode(encoded)
    except Exception:
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_DATA_URI", "Could not decode base64 image.")

    if len(image_bytes) > 20 * 1024 * 1024:
        raise AppError(status.HTTP_400_BAD_REQUEST, "FILE_TOO_LARGE", "Banner must be under 20 MB.")

    # Wrap bytes in a file-like object for the storage service
    import io
    file_obj      = io.BytesIO(image_bytes)
    file_obj.name = f"banner_{uuid.uuid4().hex}.{ext}"

    url = upload_file(file_obj, folder="events/banners", user_id=str(user.id))
    return {"success": True, "data": {"bannerUrl": url}}


# ─────────────────────────────────────────────────────────────
#  RSVP
# ─────────────────────────────────────────────────────────────
def rsvp(event_id: str, rsvp_status: str, user) -> dict:
    """
    POST /api/v1/events/<id>/rsvp/
    rsvp_status: "going" | "not_going"

    - If capacity is full and user wants "going" → placed on waitlist.
    - If user switches from "going" → "not_going" → promotes waitlist.
    """
    event    = _get_or_404(event_id)
    existing = EventRSVP.objects.filter(event=event, user=user).first()

    if existing:
        old_status              = existing.rsvp_status
        existing.rsvp_status    = rsvp_status
        existing.save(update_fields=["rsvp_status"])

        if old_status == "going" and rsvp_status == "not_going":
            Event.objects.filter(pk=event.pk).update(
                rsvp_count=max(0, event.rsvp_count - 1)
            )
            _promote_waitlist(event)
    else:
        final_status = rsvp_status
        if rsvp_status == "going" and event.capacity and event.rsvp_count >= event.capacity:
            final_status = "waitlist"

        EventRSVP.objects.create(event=event, user=user, rsvp_status=final_status)

        if final_status == "going":
            Event.objects.filter(pk=event.pk).update(rsvp_count=event.rsvp_count + 1)

    return {"success": True, "message": f"RSVP updated to: {rsvp_status}"}


# ─────────────────────────────────────────────────────────────
#  REMINDER
# ─────────────────────────────────────────────────────────────
def set_reminder(event_id: str, remind_at, user) -> dict:
    event = _get_or_404(event_id)
    if remind_at >= event.start_at:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_REMINDER",
            "Reminder must be before the event starts.",
        )
    EventReminder.objects.update_or_create(
        event=event, user=user,
        defaults={"remind_at": remind_at, "sent": False},
    )
    return {"success": True, "message": "Reminder set."}


# ─────────────────────────────────────────────────────────────
#  SAVE / UNSAVE
# ─────────────────────────────────────────────────────────────
def toggle_save(event_id: str, user) -> dict:
    _get_or_404(event_id)
    saved, created = EventSaved.objects.get_or_create(user=user, event_id=event_id)
    if not created:
        saved.delete()
        return {"success": True, "saved": False}
    return {"success": True, "saved": True}


# ─────────────────────────────────────────────────────────────
#  BROADCAST
# ─────────────────────────────────────────────────────────────
def broadcast_update(event_id: str, message: str, user) -> dict:
    event = _get_or_404(event_id)
    _assert_organiser(event, user)
    going = EventRSVP.objects.filter(event=event, rsvp_status="going").select_related("user")

    from apps.events.tasks import notify_event_update
    for rsvp_obj in going:
        notify_event_update.delay(
            str(rsvp_obj.user_id), str(event.id), event.title, message
        )

    return {"success": True, "message": f"Broadcast sent to {going.count()} attendees."}


# ─────────────────────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────
def _promote_waitlist(event: Event) -> None:
    """Move the next waitlisted user to 'going' and notify them."""
    next_in_line = (
        EventRSVP.objects
        .filter(event=event, rsvp_status="waitlist")
        .order_by("created_at")
        .first()
    )
    if next_in_line:
        next_in_line.rsvp_status = "going"
        next_in_line.save(update_fields=["rsvp_status"])
        Event.objects.filter(pk=event.pk).update(rsvp_count=event.rsvp_count + 1)

        from apps.events.tasks import notify_waitlist_promoted
        notify_waitlist_promoted.delay(
            str(next_in_line.user_id), str(event.id), event.title
        )


def _get_or_404(event_id: str) -> Event:
    event = Event.objects.filter(pk=event_id).first()
    if not event:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Event not found.")
    return event


def _assert_organiser(event: Event, user) -> None:
    if event.organiser != user and getattr(user, "role", "") != "admin":
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Only the event organiser can do this.",
        )