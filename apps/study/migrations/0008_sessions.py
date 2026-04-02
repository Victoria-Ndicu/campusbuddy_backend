"""
Migration: add StudyGroupSession, StudyGroupMessage, and is_admin to StudyGroupMember.

Run with:
    python manage.py migrate study

If you are starting fresh, run makemigrations first:
    python manage.py makemigrations study
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("study", "0001_initial"),   # adjust to your last migration name
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Add is_admin to existing StudyGroupMember ──────────────────
        migrations.AddField(
            model_name="studygroupmember",
            name="is_admin",
            field=models.BooleanField(default=False),
        ),

        # ── 2. StudyGroupSession ──────────────────────────────────────────
        migrations.CreateModel(
            name="StudyGroupSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("group", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sessions",
                    to="study.studygroup")),
                ("proposed_by", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="proposed_sessions",
                    to=settings.AUTH_USER_MODEL)),
                ("title",        models.CharField(max_length=200)),
                ("description",  models.TextField(blank=True, null=True)),
                ("location",     models.CharField(blank=True, max_length=200, null=True)),
                ("scheduled_at", models.DateTimeField()),
                ("duration_min", models.PositiveIntegerField(default=60)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "study_group_sessions",
                "ordering": ["scheduled_at"],
            },
        ),

        # ── 3. StudyGroupMessage ──────────────────────────────────────────
        migrations.CreateModel(
            name="StudyGroupMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("group", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="messages",
                    to="study.studygroup")),
                ("author", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="group_messages",
                    to=settings.AUTH_USER_MODEL)),
                ("body",       models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "study_group_messages",
                "ordering": ["created_at"],
            },
        ),
    ]