from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    label = "authentication"
    verbose_name = "Authentication"

    def ready(self):
        import logging
        from django.conf import settings

        logger = logging.getLogger("campusbuddy.notifications")

        raw = (settings.FIREBASE_SERVICE_ACCOUNT_JSON or "").strip()
        if not raw or not raw.startswith("{"):
            return

        try:
            from core.services.notification_service import init_firebase
            init_firebase()
        except Exception as exc:
            logger.error(f"Firebase init failed during app startup: {exc}")
