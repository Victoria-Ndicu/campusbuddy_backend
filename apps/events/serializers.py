"""EventBoard serializers — campus_id removed, Flutter camelCase output."""
import base64

import filetype
from rest_framework import serializers

from .models import Event, EventReminder, EventRSVP


# ── Reusable base64 image field ───────────────────────────────────────────────

class Base64ImageField(serializers.Field):
    """
    Accepts a base64-encoded image string with a data-URI prefix, e.g.:
        "data:image/png;base64,<data>"

    Validates that the payload is a real image, enforces a 20 MB size cap
    (matching the banner upload limit), and normalises the value to a
    canonical data-URI so downstream code always sees a consistent format.
    """
    ALLOWED_MIMES  = {"image/png", "image/jpeg", "image/gif", "image/webp"}
    MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB — matches upload_banner limit

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Expected a base64 string.")

        # Strip data-URI prefix if present
        if data.startswith("data:"):
            try:
                header, raw = data.split(",", 1)
                mime = header.split(":")[1].split(";")[0]  # e.g. "image/png"
            except (ValueError, IndexError):
                raise serializers.ValidationError("Malformed data-URI.")
        else:
            raw  = data
            mime = None

        # Decode
        try:
            decoded = base64.b64decode(raw, validate=True)
        except Exception:
            raise serializers.ValidationError("Invalid base64 encoding.")

        if len(decoded) > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Image exceeds {self.MAX_SIZE_BYTES // (1024 * 1024)} MB limit."
            )

        # Detect actual image type
        kind = filetype.guess(decoded)
        if kind is None or kind.mime not in self.ALLOWED_MIMES:
            detected = kind.mime if kind else "unknown"
            raise serializers.ValidationError(
                f"Unsupported image type '{detected}'. "
                f"Allowed: {self.ALLOWED_MIMES}."
            )

        # Normalise to a consistent data-URI
        normalised_mime = mime or kind.mime
        return f"data:{normalised_mime};base64,{raw}"

    def to_representation(self, value):
        return value


class EventSerializer(serializers.ModelSerializer):
    """
    Read serializer — used for GET list + detail responses.

    camelCase fields match the Flutter EBEventModel / EBEvent layers:
      id, title, description, category, location,
      startAt, endAt, rsvpCount, bannerUrl, status, createdAt,
      organiserId, organiserName,
      emoji, entry, mode          ← display-helper fields
      userRsvp, isRsvped, isSaved ← per-user flags (injected by services)
    """

    # ── IDs / relations ──────────────────────────────────────
    organiserId   = serializers.UUIDField(source="organiser_id", read_only=True)
    organiserName = serializers.SerializerMethodField()

    # ── Date-times ───────────────────────────────────────────
    startAt   = serializers.DateTimeField(source="start_at")
    endAt     = serializers.DateTimeField(source="end_at", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    # ── Counts ───────────────────────────────────────────────
    rsvpCount = serializers.IntegerField(source="rsvp_count", read_only=True)

    # ── Media ────────────────────────────────────────────────
    bannerUrl = serializers.CharField(source="banner_url", allow_null=True)

    # ── Display helpers ──────────────────────────────────────
    # These fields are stored on the model but may not exist on older
    # rows — provide safe defaults so Flutter never receives null for them.
    emoji = serializers.SerializerMethodField()
    entry = serializers.SerializerMethodField()
    mode  = serializers.SerializerMethodField()

    # ── Per-user flags (default False/None — overwritten by services) ──
    # These are NOT model fields; they are injected in _serialize_event().
    # Declaring them here ensures they appear in serializer .data output
    # when the service layer sets them, and guarantees a safe default
    # for callers that use EventSerializer directly.
    userRsvp = serializers.SerializerMethodField()
    isRsvped = serializers.SerializerMethodField()
    isSaved  = serializers.SerializerMethodField()

    class Meta:
        model  = Event
        fields = [
            # identity
            "id",
            "organiserId",
            "organiserName",
            # content
            "title",
            "description",
            "category",
            "location",
            "latitude",
            "longitude",
            # scheduling
            "startAt",
            "endAt",
            # capacity & attendance
            "capacity",
            "rsvpCount",
            # media
            "bannerUrl",
            # display helpers
            "emoji",
            "entry",
            "mode",
            # status
            "status",
            "createdAt",
            # per-user (injected by services layer)
            "userRsvp",
            "isRsvped",
            "isSaved",
        ]

    # ── Method fields ─────────────────────────────────────────

    def get_organiserName(self, obj) -> str:
        """Full name of the organiser, falling back gracefully."""
        organiser = obj.organiser
        if not organiser:
            return ""
        full = f"{getattr(organiser, 'first_name', '')} {getattr(organiser, 'last_name', '')}".strip()
        return full or getattr(organiser, "username", "") or str(organiser)

    def get_emoji(self, obj) -> str:
        return getattr(obj, "emoji", None) or "🎉"

    def get_entry(self, obj) -> str:
        return getattr(obj, "entry", None) or "Free Entry"

    def get_mode(self, obj) -> str:
        return getattr(obj, "mode", None) or "In-Person"

    # Per-user flags default to neutral values.
    # The real values are set by _serialize_event() in services.py
    # after the serializer runs, so these are only used when
    # EventSerializer is called directly (e.g. in create/update responses).
    def get_userRsvp(self, obj) -> None:
        return None

    def get_isRsvped(self, obj) -> bool:
        return False

    def get_isSaved(self, obj) -> bool:
        return False


class CreateEventSerializer(serializers.Serializer):
    """
    Validates POST /api/v1/events/ body from the Flutter create-event screen.

    Required : title, category, start_at
    Optional : description, location, latitude, longitude,
               end_at, capacity, banner_url, emoji, entry, mode
    """
    title       = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    category    = serializers.ChoiceField(
        choices=["academic", "social", "sports", "career", "other"]
    )
    location  = serializers.CharField(required=False, allow_blank=True)
    latitude  = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    start_at  = serializers.DateTimeField()
    end_at    = serializers.DateTimeField(required=False, allow_null=True)
    capacity  = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )
    # Accepts a CDN URL string OR a base64 data URI validated by Base64ImageField
    banner_url = Base64ImageField(required=False, allow_null=True)
    # Display-helper fields stored on the model
    emoji = serializers.CharField(required=False, allow_blank=True, max_length=10)
    entry = serializers.CharField(required=False, allow_blank=True, max_length=100)
    mode  = serializers.CharField(required=False, allow_blank=True, max_length=50)

    def validate(self, data):
        start = data.get("start_at")
        end   = data.get("end_at")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_at": "End time must be after start time."}
            )
        return data


class UpdateEventSerializer(serializers.Serializer):
    """Validates PATCH /api/v1/events/<id>/ body."""
    title       = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    location    = serializers.CharField(required=False, allow_blank=True)
    start_at    = serializers.DateTimeField(required=False)
    end_at      = serializers.DateTimeField(required=False, allow_null=True)
    capacity    = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )
    status = serializers.ChoiceField(
        choices=["draft", "published", "cancelled"], required=False
    )
    banner_url = Base64ImageField(required=False, allow_null=True)
    emoji = serializers.CharField(required=False, allow_blank=True, max_length=10)
    entry = serializers.CharField(required=False, allow_blank=True, max_length=100)
    mode  = serializers.CharField(required=False, allow_blank=True, max_length=50)

    def validate(self, data):
        start = data.get("start_at")
        end   = data.get("end_at")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_at": "End time must be after start time."}
            )
        return data


class RSVPSerializer(serializers.Serializer):
    """
    POST /api/v1/events/<id>/rsvp/
    Body: { "status": "going" | "not_going" }
    """
    status = serializers.ChoiceField(choices=["going", "not_going"])


class ReminderSerializer(serializers.Serializer):
    """POST /api/v1/events/reminders/"""
    event_id  = serializers.UUIDField()
    remind_at = serializers.DateTimeField()


class DeleteReminderSerializer(serializers.Serializer):
    """DELETE /api/v1/events/reminders/"""
    event_id = serializers.UUIDField()


class BroadcastSerializer(serializers.Serializer):
    """POST /api/v1/events/<id>/broadcast/"""
    message = serializers.CharField()