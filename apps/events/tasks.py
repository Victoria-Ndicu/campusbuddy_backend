from config.celery import app as celery_app


@celery_app.task(name="events.notify_update")
def notify_event_update(user_id: str, event_id: str, title: str, message: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(user_id=user_id, title=f"Update: {title}", body=message,
                           notification_type="event_update", data={"event_id": event_id})


@celery_app.task(name="events.notify_waitlist_promoted")
def notify_waitlist_promoted(user_id: str, event_id: str, title: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(user_id=user_id, title="You're in!", body=f"A spot opened for {title}",
                           notification_type="event_waitlist_promoted", data={"event_id": event_id})


@celery_app.task(name="events.send_due_reminders")
def send_due_reminders():
    """Run every 5 minutes via Celery Beat to fire event reminders."""
    from datetime import datetime, timedelta, timezone
    from apps.events.models import Event, EventReminder
    from core.services.notification_service import send_push_notification

    now     = datetime.now(timezone.utc)
    horizon = now + timedelta(minutes=5)

    due = EventReminder.objects.filter(remind_at__gte=now, remind_at__lte=horizon, sent=False).select_related("event")
    for reminder in due:
        send_push_notification(
            user_id=str(reminder.user_id),
            title=f"Reminder: {reminder.event.title}",
            body=f"Starting at {reminder.event.start_at.strftime('%H:%M')}",
            notification_type="event_reminder",
            data={"event_id": str(reminder.event_id)},
        )
        reminder.sent = True
        reminder.save(update_fields=["sent"])