"""EventBoard service layer — campus_id removed, date/month filters added."""
import base64
import uuid
import io
from rest_framework import status
from core.exceptions import AppError
from core.services.storage_service import upload_file, validate_image
from .models import Event, EventReminder, EventRSVP, EventSaved
from .serializers import EventSerializer


# ─────────────────────────────────────────────────────────────
#  INTERNAL: annotate a queryset row with per-user flags
# ─────────────────────────────────────────────────────────────
def _serialize_event(event: Event, user) -> dict:
    """
    Returns EventSerializer output + the three per-user computed fields:
      userRsvp    : "going" | "waitlist" | "not_going" | null
      isRsvped    : bool  (true when going or waitlist)
      isSaved     : bool
    """
    data = EventSerializer(event).data

    rsvp = EventRSVP.objects.filter(event=event, user=user).first()
    data["userRsvp"] = rsvp.rsvp_status if rsvp else None
    data["isRsvped"] = rsvp.rsvp_status in ("going", "waitlist") if rsvp else False

    data["isSaved"] = EventSaved.objects.filter(
        event=event, user=user
    ).exists()

    return data


# ─────────────────────────────────────────────────────────────
#  LIST
# ─────────────────────────────────────────────────────────────
def list_events(filters: dict, user):
    """
    GET /api/v1/events/

    Supported filters (all optional):
      category   – exact match, case-insensitive
      search     – title contains
      from_date  – start_at >= value  (YYYY-MM-DD or full ISO)
      date       – start_at falls on this exact date  (YYYY-MM-DD)
      month      – start_at falls in this month       (YYYY-MM)
    """
    qs = Event.objects.filter(status="published").select_related("organiser")

    if cat := filters.get("category"):
        qs = qs.filter(category__iexact=cat)

    if search := filters.get("search"):
        qs = qs.filter(title__icontains=search)

    if from_date := filters.get("from_date"):
        qs = qs.filter(start_at__gte=from_date)

    # ── exact date filter  e.g. ?date=2026-04-12 ─────────────
    if date_str := filters.get("date"):
        try:
            from datetime import date as _date
            d  = _date.fromisoformat(date_str)
            qs = qs.filter(start_at__date=d)
        except ValueError:
            pass

    # ── month filter  e.g. ?month=2026-04 ────────────────────
    if month_str := filters.get("month"):
        try:
            year, month = month_str.split("-")
            qs = qs.filter(
                start_at__year=int(year),
                start_at__month=int(month),
            )
        except (ValueError, AttributeError):
            pass

    return qs.order_by("start_at")


def list_events_serialized(filters: dict, user) -> list:
    """
    Convenience used by the paginated view — returns dicts with
    per-user isSaved / isRsvped / userRsvp already attached.
    Called from EventsView after paginating.
    """
    # NOTE: the view paginates the raw QS, then calls this on each page.
    # We expose a per-object helper so the view can call it per item.
    raise NotImplementedError("Use _serialize_event per object inside the view.")


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
    """GET /api/v1/events/<id>/"""
    event = _get_or_404(event_id)
    data  = _serialize_event(event, user)
    return {"success": True, "data": data}


# ─────────────────────────────────────────────────────────────
#  CREATE
# ─────────────────────────────────────────────────────────────
def create_event(data: dict, user) -> dict:
    """POST /api/v1/events/"""
    clean = {k: v for k, v in data.items() if v is not None and v != ""}
    event = Event.objects.create(organiser=user, status="published", **clean)
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
# ─────────────────────────────────────────────────────────────
def upload_banner(file, user) -> dict:
    validate_image(file, max_size_mb=20.0)
    url = upload_file(file, folder="events/banners", user_id=str(user.id))
    return {"success": True, "data": {"bannerUrl": url}}


def upload_banner_base64(data_uri: str, user) -> dict:
    if not data_uri or not data_uri.startswith("data:"):
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_DATA_URI",
            "Expected a base64 data URI.",
        )
    try:
        header, encoded = data_uri.split(",", 1)
        mime        = header.split(":")[1].split(";")[0]
        ext         = mime.split("/")[1]
        image_bytes = base64.b64decode(encoded)
    except Exception:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_DATA_URI",
            "Could not decode base64 image.",
        )
    if len(image_bytes) > 20 * 1024 * 1024:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "FILE_TOO_LARGE",
            "Banner must be under 20 MB.",
        )
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
    """
    event    = _get_or_404(event_id)
    existing = EventRSVP.objects.filter(event=event, user=user).first()

    if existing:
        old_status           = existing.rsvp_status
        existing.rsvp_status = rsvp_status
        existing.save(update_fields=["rsvp_status"])

        if old_status == "going" and rsvp_status == "not_going":
            Event.objects.filter(pk=event.pk).update(
                rsvp_count=max(0, event.rsvp_count - 1)
            )
            _promote_waitlist(event)
    else:
        final_status = rsvp_status
        if (
            rsvp_status == "going"
            and event.capacity
            and event.rsvp_count >= event.capacity
        ):
            final_status = "waitlist"

        EventRSVP.objects.create(event=event, user=user, rsvp_status=final_status)

        if final_status == "going":
            Event.objects.filter(pk=event.pk).update(
                rsvp_count=event.rsvp_count + 1
            )

    return {"success": True, "message": f"RSVP updated to: {rsvp_status}"}


# ─────────────────────────────────────────────────────────────
#  REMINDER  (set / delete)
# ─────────────────────────────────────────────────────────────
def set_reminder(event_id: str, remind_at, user) -> dict:
    """POST /api/v1/events/reminders/"""
    event = _get_or_404(event_id)
    if remind_at >= event.start_at:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_REMINDER",
            "Reminder must be before the event starts.",
        )
    EventReminder.objects.update_or_create(
        event=event,
        user=user,
        defaults={"remind_at": remind_at, "sent": False},
    )
    return {"success": True, "message": "Reminder set."}


def delete_reminder(event_id: str, user) -> dict:
    """DELETE /api/v1/events/reminders/"""
    deleted, _ = EventReminder.objects.filter(
        event_id=event_id, user=user
    ).delete()
    if not deleted:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            "No reminder found for this event.",
        )
    return {"success": True, "message": "Reminder removed."}


# ─────────────────────────────────────────────────────────────
#  SAVE / UNSAVE
# ─────────────────────────────────────────────────────────────
def toggle_save(event_id: str, user) -> dict:
    _get_or_404(event_id)
    saved, created = EventSaved.objects.get_or_create(
        user=user, event_id=event_id
    )
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
    going = EventRSVP.objects.filter(
        event=event, rsvp_status="going"
    ).select_related("user")

    from apps.events.tasks import notify_event_update
    for rsvp_obj in going:
        notify_event_update.delay(
            str(rsvp_obj.user_id), str(event.id), event.title, message
        )
    return {
        "success": True,
        "message": f"Broadcast sent to {going.count()} attendees.",
    }


# ─────────────────────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────
def _promote_waitlist(event: Event) -> None:
    next_in_line = (
        EventRSVP.objects.filter(event=event, rsvp_status="waitlist")
        .order_by("created_at")
        .first()
    )
    if next_in_line:
        next_in_line.rsvp_status = "going"
        next_in_line.save(update_fields=["rsvp_status"])
        Event.objects.filter(pk=event.pk).update(
            rsvp_count=event.rsvp_count + 1
        )
        from apps.events.tasks import notify_waitlist_promoted
        notify_waitlist_promoted.delay(
            str(next_in_line.user_id), str(event.id), event.title
        )


def _get_or_404(event_id: str) -> Event:
    event = Event.objects.filter(pk=event_id).first()
    if not event:
        raise AppError(
            status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Event not found."
        )
    return event


def _assert_organiser(event: Event, user) -> None:
    if event.organiser != user and getattr(user, "role", "") != "admin":
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "Only the event organiser can do this.",
        )