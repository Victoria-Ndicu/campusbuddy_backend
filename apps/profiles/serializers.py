from rest_framework import serializers
from .models import DeviceToken, Feedback, Notification, UserPreferences


class UserPreferencesSerializer(serializers.ModelSerializer):
    darkMode      = serializers.BooleanField(source="dark_mode", required=False)
    notifications = serializers.BooleanField(required=False)
    language      = serializers.CharField(max_length=10, required=False)

    class Meta:
        model  = UserPreferences
        fields = ["notifications", "darkMode", "language"]


class ProfileSerializer(serializers.Serializer):
    """Read-only combined profile + preferences payload."""
    id            = serializers.UUIDField()
    fullName      = serializers.CharField(source="full_name", allow_null=True)
    email         = serializers.EmailField()
    phone         = serializers.CharField(allow_null=True)
    degree        = serializers.CharField(allow_null=True)
    yearOfStudy   = serializers.IntegerField(source="year_of_study", allow_null=True)
    university    = serializers.CharField(allow_null=True)
    avatarUrl     = serializers.URLField(source="avatar_url", allow_null=True)
    isVerified    = serializers.BooleanField(source="is_verified")
    role          = serializers.CharField()
    createdAt     = serializers.DateTimeField(source="created_at")
    preferences   = serializers.SerializerMethodField()

    def get_preferences(self, obj):
        try:
            prefs = obj.preferences
            return {"notifications": prefs.notifications, "darkMode": prefs.dark_mode, "language": prefs.language}
        except UserPreferences.DoesNotExist:
            return {"notifications": True, "darkMode": False, "language": "en"}


class UpdateProfileSerializer(serializers.Serializer):
    fullName    = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone       = serializers.CharField(max_length=30,  required=False, allow_blank=True)
    degree      = serializers.CharField(max_length=120, required=False, allow_blank=True)
    yearOfStudy = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=10)
    university  = serializers.CharField(max_length=160, required=False, allow_blank=True)


class UpdatePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    newPassword     = serializers.CharField(min_length=8)


class UpdatePreferencesSerializer(serializers.Serializer):
    notifications = serializers.BooleanField(required=False)
    darkMode      = serializers.BooleanField(required=False)
    language      = serializers.CharField(max_length=10, required=False)


class DeviceTokenSerializer(serializers.Serializer):
    token    = serializers.CharField(max_length=512)
    platform = serializers.ChoiceField(choices=["android", "ios"])


class FeedbackSerializer(serializers.Serializer):
    message  = serializers.CharField()
    category = serializers.CharField(max_length=30, default="other")


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ["id", "title", "body", "notification_type", "read", "data", "created_at"]