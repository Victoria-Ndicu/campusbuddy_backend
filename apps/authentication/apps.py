from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    label = "authentication"
    verbose_name = "Authentication"

    def ready(self):
        # Initialise Firebase once Django is fully loaded
        from core.services.notification_service import init_firebase
        init_firebase()