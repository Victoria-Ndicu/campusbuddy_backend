"""EventBoard service layer."""
from rest_framework import status
from core.exceptions import AppError
from core.services.storage_service import upload_file, validate_image
from .models import Event, EventReminder, EventRSVP, EventSaved
from .serializers import EventSerializer


def list_events(filters: dict, user):
    qs = Event.objects.filter(status="published")
    if filters.get("campus_id"):
        qs = qs.filter(campus_id=filters["campus_id"])
    if filters.get("category"):
        qs = qs.filter(category=filters["category"])
    if filters.get("search"):
        qs = qs.filter(title__icontains=filters["search"])
    if filters.get("from_date"):
        qs = qs.filter(start_at__gte=filters["from_date"])
    return qs


def get_event(event_id: str, user) -> dict:
    event = _get_or_404(event_id)
    data  = EventSerializer(event).data
    rsvp  = EventRSVP.objects.filter(event=event, user=user).first()
    data["userRsvp"] = rsvp.rsvp_status if rsvp else None
    return {"success": True, "data": data}


def create_event(data: dict, user) -> dict:
    event = Event.objects.create(organiser=user, **{k: v for k, v in data.items() if v is not None})
    return {"success": True, "data": EventSerializer(event).data}


def update_event(event_id: str, data: dict, user) -> dict:
    event = _get_or_404(event_id)
    _assert_organiser(event, user)
    for field, value in data.items():
        setattr(event, field, value)
    event.save()
    return {"success": True, "data": EventSerializer(event).data}


def delete_event(event_id: str, user) -> dict:
    event = _get_or_404(event_id)
    _assert_organiser(event, user)
    event.status = "cancelled"
    event.save(update_fields=["status"])
    return {"success": True, "message": "Event cancelled."}


def upload_banner(file, user) -> dict:
    validate_image(file, max_size_mb=20.0)
    url = upload_file(file, folder="events", user_id=str(user.id))
    return {"success": True, "data": {"bannerUrl": url}}


def rsvp(event_id: str, rsvp_status: str, user) -> dict:
    event = _get_or_404(event_id)
    existing = EventRSVP.objects.filter(event=event, user=user).first()

    if existing:
        old_status = existing.rsvp_status
        existing.rsvp_status = rsvp_status
        existing.save(update_fields=["rsvp_status"])
        if old_status == "going" and rsvp_status == "not_going":
            Event.objects.filter(pk=event.pk).update(rsvp_count=max(0, event.rsvp_count - 1))
            _promote_waitlist(event)
    else:
        final_status = rsvp_status
        if rsvp_status == "going" and event.capacity and event.rsvp_count >= event.capacity:
            final_status = "waitlist"
        EventRSVP.objects.create(event=event, user=user, rsvp_status=final_status)
        if final_status == "going":
            Event.objects.filter(pk=event.pk).update(rsvp_count=event.rsvp_count + 1)

    return {"success": True, "message": f"RSVP updated to: {rsvp_status}"}


def set_reminder(event_id: str, remind_at, user) -> dict:
    event = _get_or_404(event_id)
    if remind_at >= event.start_at:
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_REMINDER", "Reminder must be before the event starts.")
    EventReminder.objects.update_or_create(
        event=event, user=user,
        defaults={"remind_at": remind_at, "sent": False},
    )
    return {"success": True, "message": "Reminder set."}


def toggle_save(event_id: str, user) -> dict:
    _get_or_404(event_id)
    saved, created = EventSaved.objects.get_or_create(user=user, event_id=event_id)
    if not created:
        saved.delete()
        return {"success": True, "saved": False}
    return {"success": True, "saved": True}


def broadcast_update(event_id: str, message: str, user) -> dict:
    event = _get_or_404(event_id)
    _assert_organiser(event, user)
    going = EventRSVP.objects.filter(event=event, rsvp_status="going").select_related("user")
    from apps.events.tasks import notify_event_update
    for rsvp in going:
        notify_event_update.delay(str(rsvp.user_id), str(event.id), event.title, message)
    return {"success": True, "message": f"Broadcast sent to {going.count()} attendees."}


def _promote_waitlist(event: Event) -> None:
    next_in_line = EventRSVP.objects.filter(event=event, rsvp_status="waitlist").order_by("created_at").first()
    if next_in_line:
        next_in_line.rsvp_status = "going"
        next_in_line.save(update_fields=["rsvp_status"])
        Event.objects.filter(pk=event.pk).update(rsvp_count=event.rsvp_count + 1)
        from apps.events.tasks import notify_waitlist_promoted
        notify_waitlist_promoted.delay(str(next_in_line.user_id), str(event.id), event.title)


def _get_or_404(event_id: str) -> Event:
    event = Event.objects.filter(pk=event_id).first()
    if not event:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Event not found.")
    return event


def _assert_organiser(event: Event, user) -> None:
    if event.organiser != user and getattr(user, "role", "") != "admin":
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Only the event organiser can do this.")