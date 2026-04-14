"""
Initial migration for the authentication app.
Creates AllowedEmailDomain, User, and OtpCode tables.
university is a ForeignKey to AllowedEmailDomain from the start.
"""
import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        # ── AllowedEmailDomain ─────────────────────────────────────────────────
        migrations.CreateModel(
            name="AllowedEmailDomain",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(max_length=255, unique=True)),
                ("institution_name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["institution_name"],
            },
        ),

        # ── User ───────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(
                    default=False,
                    help_text="Designates that this user has all permissions without explicitly assigning them.",
                    verbose_name="superuser status",
                )),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("phone", models.CharField(blank=True, max_length=30, null=True)),
                ("role", models.CharField(
                    choices=[("student", "Student"), ("admin", "Admin")],
                    default="student",
                    max_length=20,
                )),
                ("is_verified", models.BooleanField(default=False)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(blank=True, max_length=120, null=True)),
                ("degree", models.CharField(blank=True, max_length=120, null=True)),
                ("year_of_study", models.SmallIntegerField(blank=True, null=True)),
                ("university", models.ForeignKey(
                    blank=True,
                    help_text="Set automatically from the user's email domain at registration.",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="users",
                    to="authentication.allowedemailDomain",
                )),
                ("avatar_url", models.URLField(blank=True, max_length=500, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("groups", models.ManyToManyField(
                    blank=True,
                    help_text="The groups this user belongs to.",
                    related_name="user_set",
                    related_query_name="user",
                    to="auth.group",
                    verbose_name="groups",
                )),
                ("user_permissions", models.ManyToManyField(
                    blank=True,
                    help_text="Specific permissions for this user.",
                    related_name="user_set",
                    related_query_name="user",
                    to="auth.permission",
                    verbose_name="user permissions",
                )),
            ],
            options={
                "db_table": "users",
                "ordering": ["-created_at"],
            },
        ),

        # ── OtpCode ────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="OtpCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="otp_codes",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("code", models.CharField(max_length=255)),
                ("otp_type", models.CharField(
                    choices=[("email_verify", "Email Verification"), ("password_reset", "Password Reset")],
                    max_length=30,
                )),
                ("expires_at", models.DateTimeField()),
                ("used", models.BooleanField(default=False)),
                ("attempts", models.SmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "otp_codes",
                "ordering": ["-created_at"],
            },
        ),
    ]
