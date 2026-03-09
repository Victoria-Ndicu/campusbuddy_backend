import uuid
from django.conf import settings
from django.db import models


class UserPreferences(models.Model):
    """One-to-one preferences record per user."""
    user          = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences", primary_key=True)
    notifications = models.BooleanField(default=True)
    dark_mode     = models.BooleanField(default=False)
    language      = models.CharField(max_length=10, default="en")
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preferences"


class DeviceToken(models.Model):
    """FCM / APNs push notification tokens. Shared with all notification-sending apps."""
    PLATFORM_CHOICES = [("android", "Android"), ("ios", "iOS")]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens")
    token      = models.CharField(max_length=512, unique=True)
    platform   = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    active     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_tokens"


class Notification(models.Model):
    """Shared in-app notification record. Written by all modules, read via profile."""
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title             = models.CharField(max_length=200)
    body              = models.TextField()
    notification_type = models.CharField(max_length=50)   # market_message | event_reminder | ...
    read              = models.BooleanField(default=False)
    data              = models.JSONField(default=dict, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = "notifications"
        ordering  = ["-created_at"]
        indexes   = [models.Index(fields=["user", "read"])]


class Feedback(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="feedback")
    message    = models.TextField()
    category   = models.CharField(max_length=30, default="other")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feedback"


class AuditLog(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action     = models.CharField(max_length=60)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]