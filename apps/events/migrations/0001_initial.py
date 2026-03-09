from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id",          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",       models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, null=True)),
                ("category",    models.CharField(choices=[("academic","Academic"),("social","Social"),("sports","Sports"),("career","Career"),("other","Other")], max_length=50)),
                ("location",    models.CharField(blank=True, max_length=200, null=True)),
                ("latitude",    models.CharField(blank=True, max_length=20, null=True)),
                ("longitude",   models.CharField(blank=True, max_length=20, null=True)),
                ("start_at",    models.DateTimeField(db_index=True)),
                ("end_at",      models.DateTimeField(blank=True, null=True)),
                ("capacity",    models.PositiveIntegerField(blank=True, null=True)),
                ("rsvp_count",  models.PositiveIntegerField(default=0)),
                ("banner_url",  models.URLField(blank=True, max_length=500, null=True)),
                ("campus_id",   models.CharField(db_index=True, max_length=80)),
                ("status",      models.CharField(choices=[("draft","Draft"),("published","Published"),("cancelled","Cancelled")], default="published", max_length=20)),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
                ("organiser",   models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="organised_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "events", "ordering": ["start_at"]},
        ),
        migrations.CreateModel(
            name="EventRSVP",
            fields=[
                ("id",          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rsvp_status", models.CharField(choices=[("going","Going"),("not_going","Not Going"),("waitlist","Waitlist")], default="going", max_length=20)),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
                ("event",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="rsvps", to="events.event")),
                ("user",        models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="event_rsvps", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "event_rsvps"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="EventReminder",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("remind_at",  models.DateTimeField()),
                ("sent",       models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("event",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="reminders", to="events.event")),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="event_reminders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "event_reminders"},
        ),
        migrations.AddIndex(
            model_name="eventreminder",
            index=models.Index(fields=["remind_at","sent"], name="reminder_due_idx"),
        ),
        migrations.CreateModel(
            name="EventSaved",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("event",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_by", to="events.event")),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "events_saved"},
            bases=(models.Model,),
        ),
        migrations.AddConstraint(
            model_name="eventrsvp",
            constraint=models.UniqueConstraint(fields=["event","user"], name="unique_event_rsvp"),
        ),
        migrations.AddConstraint(
            model_name="eventsaved",
            constraint=models.UniqueConstraint(fields=["user","event"], name="unique_user_saved_event"),
        ),
    ]
