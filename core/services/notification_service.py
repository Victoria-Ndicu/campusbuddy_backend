"""
Shared push-notification service.
All apps call send_push_notification() — never directly touch Firebase.
"""
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("campusbuddy.notifications")


def send_push_notification(
    user_id,
    title: str,
    body: str,
    notification_type: str,
    data: Optional[dict[str, Any]] = None,
    persist: bool = True,
) -> None:
    """
    Send an FCM push notification to all active devices for a user
    and optionally write an in-app notification row.

    This is always called inside a task (see apps/*/tasks.py) so it
    doesn't block the request cycle.
    """
    from apps.profiles.models import DeviceToken
    from apps.authentication.models import User

    try:
        user = User.objects.get(pk=user_id, deleted_at__isnull=True)
    except User.DoesNotExist:
        logger.warning(f"Notification skipped — user {user_id} not found")
        return

    # Persist in-app notification
    if persist:
        from apps.profiles.models import Notification
        Notification.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            data=data or {},
        )

    # Fetch active FCM tokens
    tokens = list(
        DeviceToken.objects.filter(user=user, active=True).values_list("token", flat=True)
    )
    if not tokens:
        return

    # Send via Firebase Admin SDK
    try:
        import firebase_admin
        from firebase_admin import messaging

        messages = [
            messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
            )
            for token in tokens
        ]
        response = messaging.send_each(messages)
        logger.info(
            f"Push sent to user {user_id}: "
            f"{response.success_count} ok, {response.failure_count} failed"
        )
    except Exception as exc:
        logger.error(f"FCM send error for user {user_id}: {exc}")


def init_firebase() -> None:
    """Initialise Firebase Admin SDK once. Safe to call multiple times."""
    from django.conf import settings
    import firebase_admin

    if firebase_admin._apps:
        return
    if not settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        logger.warning("Firebase not configured — push notifications disabled.")
        return
    try:
        from firebase_admin import credentials

        # FIREBASE_SERVICE_ACCOUNT_JSON is a JSON string in env — parse it to dict
        service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialised.")
    except json.JSONDecodeError as exc:
        logger.error(f"Firebase init failed — invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {exc}")
    except Exception as exc:
        logger.error(f"Firebase init failed: {exc}")