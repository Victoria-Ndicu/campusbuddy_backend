"""Profile service — all profile business logic."""
from datetime import datetime, timezone

from django.contrib.auth.hashers import check_password
from rest_framework import status

from core.exceptions import AppError
from core.services.storage_service import delete_file, upload_file, validate_image

from .models import AuditLog, DeviceToken, Feedback, UserPreferences


def get_profile(user) -> dict:
    from .serializers import ProfileSerializer
    return {"success": True, "data": ProfileSerializer(user).data}


def update_profile(user, data: dict) -> dict:
    mapping = {
        "fullName": "full_name",
        "phone": "phone",
        "degree": "degree",
        "yearOfStudy": "year_of_study",
        "university": "university",
    }
    fields_updated = []
    for key, model_field in mapping.items():
        if key in data:
            setattr(user, model_field, data[key] or None)
            fields_updated.append(model_field)

    if fields_updated:
        user.save(update_fields=fields_updated + ["updated_at"])

    from .serializers import ProfileSerializer
    return {"success": True, "message": "Profile updated.", "user": ProfileSerializer(user).data}


def upload_avatar(user, file) -> dict:
    validate_image(file)
    old_url = user.avatar_url
    new_url = upload_file(file, folder="avatars", user_id=str(user.id))
    user.avatar_url = new_url
    user.save(update_fields=["avatar_url"])
    if old_url:
        delete_file(old_url)
    return {"success": True, "avatarUrl": new_url}


def change_password(user, current_password: str, new_password: str) -> dict:
    if not user.check_password(current_password):
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_PASSWORD", "Current password is incorrect.")
    user.set_password(new_password)
    user.save(update_fields=["password"])
    # Blacklist all refresh tokens (force re-login on other devices)
    from apps.authentication.services import _blacklist_all_tokens
    _blacklist_all_tokens(user)
    return {"success": True, "message": "Password updated successfully."}


def update_preferences(user, data: dict) -> dict:
    prefs, _ = UserPreferences.objects.get_or_create(user=user)
    if "notifications" in data:
        prefs.notifications = data["notifications"]
        # Toggle all device tokens
        DeviceToken.objects.filter(user=user).update(active=data["notifications"])
    if "darkMode" in data:
        prefs.dark_mode = data["darkMode"]
    if "language" in data:
        prefs.language = data["language"]
    prefs.save()
    return {
        "success": True,
        "preferences": {
            "notifications": prefs.notifications,
            "darkMode": prefs.dark_mode,
            "language": prefs.language,
        },
    }


def register_device_token(user, token: str, platform: str) -> dict:
    DeviceToken.objects.update_or_create(
        token=token,
        defaults={"user": user, "platform": platform, "active": True},
    )
    return {"success": True, "message": "Device registered."}


def submit_feedback(user, message: str, category: str) -> dict:
    Feedback.objects.create(user=user, message=message, category=category)
    from core.services.email_service import send_email
    from django.conf import settings
    send_email(
        to=settings.DEFAULT_FROM_EMAIL,
        subject=f"[CampusBuddy Feedback] {category}",
        html_body=f"<p>From: {user.email}</p><p>{message}</p>",
    )
    return {"success": True, "message": "Thank you for your feedback."}


def delete_account(user, password: str, ip_address=None) -> dict:
    if not user.check_password(password):
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_PASSWORD", "Password confirmation failed.")

    now = datetime.now(timezone.utc)
    user.deleted_at = now
    user.full_name  = "Deleted User"
    user.email      = f"deleted_{user.id}@deleted.invalid"
    user.phone      = None
    user.avatar_url = None
    user.save()

    AuditLog.objects.create(user=user, action="account_deleted", ip_address=ip_address)

    from apps.authentication.services import _blacklist_all_tokens
    _blacklist_all_tokens(user)

    return {"success": True, "message": "Your account has been scheduled for deletion."}