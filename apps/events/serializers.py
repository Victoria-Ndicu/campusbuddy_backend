"""EventBoard serializers — campus_id removed."""
from rest_framework import serializers
from .models import Event, EventReminder, EventRSVP


class EventSerializer(serializers.ModelSerializer):
    """
    Read serializer — used for GET responses and inside services.py.
    camelCase output matches the Flutter model layer.
    """
    organiserId = serializers.UUIDField(source="organiser_id", read_only=True)
    startAt     = serializers.DateTimeField(source="start_at")
    endAt       = serializers.DateTimeField(source="end_at", allow_null=True)
    rsvpCount   = serializers.IntegerField(source="rsvp_count", read_only=True)
    bannerUrl   = serializers.CharField(source="banner_url", allow_null=True)
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = Event
        fields = [
            "id", "organiserId", "title", "description", "category",
            "location", "latitude", "longitude",
            "startAt", "endAt", "capacity", "rsvpCount",
            "bannerUrl", "status", "createdAt",
        ]


class CreateEventSerializer(serializers.Serializer):
    """
    Validates POST /api/v1/events/ body from the Flutter create-event screen.

    Required: title, category, start_at
    Optional: description, location, latitude, longitude,
              end_at, capacity, banner_url
    """
    title       = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    category    = serializers.ChoiceField(
        choices=["academic", "social", "sports", "career", "other"]
    )
    location    = serializers.CharField(required=False, allow_blank=True)
    latitude    = serializers.FloatField(required=False, allow_null=True)
    longitude   = serializers.FloatField(required=False, allow_null=True)
    start_at    = serializers.DateTimeField()
    end_at      = serializers.DateTimeField(required=False, allow_null=True)
    capacity    = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    # banner_url accepts either a CDN URL or a base64 data URI
    banner_url  = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=2_000_000
    )

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
    capacity    = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    status      = serializers.ChoiceField(
        choices=["draft", "published", "cancelled"], required=False
    )
    banner_url  = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=2_000_000
    )

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


class BroadcastSerializer(serializers.Serializer):
    """POST /api/v1/events/<id>/broadcast/"""
    message = serializers.CharField()