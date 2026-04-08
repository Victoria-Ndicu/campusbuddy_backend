"""EventBoard serializers — campus_id removed, Flutter camelCase output."""
from rest_framework import serializers
from .models import Event, EventReminder, EventRSVP


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
    # Accepts a short CDN URL or a long base64 data URI
    banner_url = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=2_000_000
    )
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
    banner_url = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=2_000_000
    )
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