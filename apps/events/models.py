"""EventBoard models — campus_id removed."""
import uuid
from django.conf import settings
from django.db import models


class Event(models.Model):
    CATEGORY_CHOICES = [
        ("academic", "Academic"),
        ("social",   "Social"),
        ("sports",   "Sports"),
        ("career",   "Career"),
        ("other",    "Other"),
    ]
    STATUS_CHOICES = [
        ("draft",      "Draft"),
        ("published",  "Published"),
        ("cancelled",  "Cancelled"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organiser   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organised_events",
    )
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location    = models.CharField(max_length=200, blank=True, null=True)
    latitude    = models.CharField(max_length=20,  blank=True, null=True)
    longitude   = models.CharField(max_length=20,  blank=True, null=True)
    start_at    = models.DateTimeField(db_index=True)
    end_at      = models.DateTimeField(null=True, blank=True)
    capacity    = models.PositiveIntegerField(null=True, blank=True)
    rsvp_count  = models.PositiveIntegerField(default=0)
    # banner_url stores either:
    #   • a CDN/S3 URL returned by the upload endpoint  (preferred)
    #   • a base64 data URI as a fallback when upload fails
    # max_length=2_000_000 accommodates base64-encoded images up to ~1.5 MB.
    # For larger images always use the upload endpoint so a real URL is stored.
    banner_url  = models.TextField(blank=True, null=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default="published")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "events"
        ordering = ["start_at"]

    @property
    def owner(self):
        return self.organiser

    def __str__(self):
        return f"{self.title} ({self.start_at:%Y-%m-%d})"


class EventRSVP(models.Model):
    STATUS_CHOICES = [
        ("going",     "Going"),
        ("not_going", "Not Going"),
        ("waitlist",  "Waitlist"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event       = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_rsvps",
    )
    rsvp_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="going")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "event_rsvps"
        unique_together = [["event", "user"]]

    def __str__(self):
        return f"{self.user} → {self.event.title} ({self.rsvp_status})"


class EventReminder(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event     = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reminders")
    user      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_reminders",
    )
    remind_at = models.DateTimeField()
    sent      = models.BooleanField(default=False)
    created_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_reminders"
        indexes  = [models.Index(fields=["remind_at", "sent"])]


class EventSaved(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_events",
    )
    event      = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "events_saved"
        unique_together = [["user", "event"]]