from rest_framework import serializers
from .models import Event, EventReminder, EventRSVP


class EventSerializer(serializers.ModelSerializer):
    organiserId = serializers.UUIDField(source="organiser_id", read_only=True)
    startAt     = serializers.DateTimeField(source="start_at")
    endAt       = serializers.DateTimeField(source="end_at", allow_null=True)
    rsvpCount   = serializers.IntegerField(source="rsvp_count", read_only=True)
    bannerUrl   = serializers.URLField(source="banner_url", allow_null=True)
    campusId    = serializers.CharField(source="campus_id")
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = Event
        fields = [
            "id", "organiserId", "title", "description", "category",
            "location", "latitude", "longitude", "startAt", "endAt",
            "capacity", "rsvpCount", "bannerUrl", "campusId", "status", "createdAt",
        ]


class CreateEventSerializer(serializers.Serializer):
    title       = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False)
    category    = serializers.ChoiceField(choices=["academic", "social", "sports", "career", "other"])
    location    = serializers.CharField(required=False)
    latitude    = serializers.FloatField(required=False, allow_null=True)
    longitude   = serializers.FloatField(required=False, allow_null=True)
    start_at    = serializers.DateTimeField()
    end_at      = serializers.DateTimeField(required=False, allow_null=True)
    capacity    = serializers.IntegerField(required=False, allow_null=True)
    campus_id   = serializers.CharField(max_length=80)


class UpdateEventSerializer(serializers.Serializer):
    title       = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    location    = serializers.CharField(required=False)
    start_at    = serializers.DateTimeField(required=False)
    end_at      = serializers.DateTimeField(required=False, allow_null=True)
    capacity    = serializers.IntegerField(required=False, allow_null=True)
    status      = serializers.ChoiceField(choices=["draft", "published", "cancelled"], required=False)


class RSVPSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["going", "not_going"])


class ReminderSerializer(serializers.Serializer):
    event_id  = serializers.UUIDField()
    remind_at = serializers.DateTimeField()


class BroadcastSerializer(serializers.Serializer):
    message = serializers.CharField()