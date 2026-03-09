from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="UserPreferences",
            fields=[
                ("user",          models.OneToOneField(on_delete=models.deletion.CASCADE, primary_key=True, related_name="preferences", serialize=False, to=settings.AUTH_USER_MODEL)),
                ("notifications", models.BooleanField(default=True)),
                ("dark_mode",     models.BooleanField(default=False)),
                ("language",      models.CharField(default="en", max_length=10)),
                ("updated_at",    models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "user_preferences"},
        ),
        migrations.CreateModel(
            name="DeviceToken",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("token",      models.CharField(max_length=512, unique=True)),
                ("platform",   models.CharField(choices=[("android","Android"),("ios","iOS")], max_length=10)),
                ("active",     models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="device_tokens", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "device_tokens"},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id",                models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",             models.CharField(max_length=200)),
                ("body",              models.TextField()),
                ("notification_type", models.CharField(max_length=50)),
                ("read",              models.BooleanField(default=False)),
                ("data",              models.JSONField(blank=True, default=dict)),
                ("created_at",        models.DateTimeField(auto_now_add=True)),
                ("user",              models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "notifications", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["user", "read"], name="notif_user_read_idx"),
        ),
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("message",    models.TextField()),
                ("category",   models.CharField(default="other", max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user",       models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, related_name="feedback", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "feedback"},
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action",     models.CharField(max_length=60)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user",       models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "audit_log", "ordering": ["-created_at"]},
        ),
    ]
