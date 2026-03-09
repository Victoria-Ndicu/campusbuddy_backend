#!/bin/bash
# Run from inside campusbuddy_django/

# ── authentication ─────────────────────────────────────────────────────────────
cat > apps/authentication/migrations/0001_initial.py << 'EOF'
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password",        models.CharField(max_length=128, verbose_name="password")),
                ("last_login",       models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("id",               models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email",            models.EmailField(db_index=True, max_length=254, unique=True)),
                ("phone",            models.CharField(blank=True, max_length=30, null=True)),
                ("role",             models.CharField(choices=[("student","Student"),("admin","Admin")], default="student", max_length=20)),
                ("is_verified",      models.BooleanField(default=False)),
                ("is_staff",         models.BooleanField(default=False)),
                ("is_active",        models.BooleanField(default=True)),
                ("is_superuser",     models.BooleanField(default=False)),
                ("full_name",        models.CharField(blank=True, max_length=120, null=True)),
                ("degree",           models.CharField(blank=True, max_length=120, null=True)),
                ("year_of_study",    models.SmallIntegerField(blank=True, null=True)),
                ("university",       models.CharField(blank=True, max_length=160, null=True)),
                ("avatar_url",       models.URLField(blank=True, max_length=500, null=True)),
                ("deleted_at",       models.DateTimeField(blank=True, null=True)),
                ("created_at",       models.DateTimeField(auto_now_add=True)),
                ("updated_at",       models.DateTimeField(auto_now=True)),
                ("groups",           models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"db_table": "users", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OtpCode",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code",       models.CharField(max_length=255)),
                ("otp_type",   models.CharField(choices=[("email_verify","Email Verification"),("password_reset","Password Reset")], max_length=30)),
                ("expires_at", models.DateTimeField()),
                ("used",       models.BooleanField(default=False)),
                ("attempts",   models.SmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="otp_codes", to="authentication.user")),
            ],
            options={"db_table": "otp_codes", "ordering": ["-created_at"]},
        ),
    ]
EOF

# ── profiles ───────────────────────────────────────────────────────────────────
cat > apps/profiles/migrations/0001_initial.py << 'EOF'
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
EOF

# ── market ─────────────────────────────────────────────────────────────────────
cat > apps/market/migrations/0001_initial.py << 'EOF'
from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="MarketListing",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",        models.CharField(max_length=200)),
                ("description",  models.TextField(blank=True, null=True)),
                ("price",        models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("category",     models.CharField(max_length=50)),
                ("condition",    models.CharField(blank=True, choices=[("new","New"),("like_new","Like New"),("good","Good"),("fair","Fair")], max_length=20, null=True)),
                ("campus_id",    models.CharField(db_index=True, max_length=80)),
                ("listing_type", models.CharField(choices=[("sale","Sale"),("donation","Donation")], default="sale", max_length=20)),
                ("status",       models.CharField(choices=[("active","Active"),("sold","Sold"),("donated","Donated"),("removed","Removed")], db_index=True, default="active", max_length=20)),
                ("image_urls",   models.JSONField(blank=True, default=list)),
                ("view_count",   models.PositiveIntegerField(default=0)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("seller",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_listings", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="MarketMessage",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body",       models.TextField()),
                ("channel",    models.CharField(choices=[("in_app","In-App"),("whatsapp","WhatsApp"),("email","Email")], default="in_app", max_length=20)),
                ("read",       models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="messages", to="market.marketlisting")),
                ("receiver",   models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="received_market_messages", to=settings.AUTH_USER_MODEL)),
                ("sender",     models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="sent_market_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_messages", "ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="MarketSavedListing",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_by", to="market.marketlisting")),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_saved_listings"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MarketReview",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rating",     models.SmallIntegerField()),
                ("comment",    models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("buyer",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="market_reviews_given", to=settings.AUTH_USER_MODEL)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="reviews", to="market.marketlisting")),
                ("seller",     models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="market_reviews_received", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_reviews"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MarketDonationClaim",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status",     models.CharField(choices=[("pending","Pending"),("confirmed","Confirmed"),("rejected","Rejected")], default="pending", max_length=20)),
                ("message",    models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("claimant",   models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="donation_claims", to=settings.AUTH_USER_MODEL)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="donation_claims", to="market.marketlisting")),
            ],
            options={"db_table": "market_donation_claims"},
            bases=(models.Model,),
        ),
        migrations.AddConstraint(
            model_name="marketsavedlisting",
            constraint=models.UniqueConstraint(fields=["user","listing"], name="unique_user_saved_listing"),
        ),
        migrations.AddConstraint(
            model_name="marketreview",
            constraint=models.UniqueConstraint(fields=["buyer","listing"], name="unique_buyer_listing_review"),
        ),
        migrations.AddConstraint(
            model_name="marketdonationclaim",
            constraint=models.UniqueConstraint(fields=["claimant","listing"], name="unique_claimant_listing"),
        ),
    ]
EOF

# ── housing ────────────────────────────────────────────────────────────────────
cat > apps/housing/migrations/0001_initial.py << 'EOF'
from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="HousingListing",
            fields=[
                ("id",             models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",          models.CharField(max_length=200)),
                ("description",    models.TextField(blank=True, null=True)),
                ("rent_per_month", models.DecimalField(decimal_places=2, max_digits=10)),
                ("location_name",  models.CharField(max_length=200)),
                ("latitude",       models.DecimalField(decimal_places=7, max_digits=10)),
                ("longitude",      models.DecimalField(decimal_places=7, max_digits=10)),
                ("bedrooms",       models.SmallIntegerField(blank=True, null=True)),
                ("bathrooms",      models.SmallIntegerField(blank=True, null=True)),
                ("amenities",      models.JSONField(blank=True, default=list)),
                ("image_urls",     models.JSONField(blank=True, default=list)),
                ("available_from", models.DateField(blank=True, null=True)),
                ("status",         models.CharField(choices=[("active","Active"),("rented","Rented"),("removed","Removed")], db_index=True, default="active", max_length=20)),
                ("campus_id",      models.CharField(db_index=True, max_length=80)),
                ("created_at",     models.DateTimeField(auto_now_add=True)),
                ("updated_at",     models.DateTimeField(auto_now=True)),
                ("landlord",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="housing_listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "housing_listings", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="RoommateProfile",
            fields=[
                ("id",             models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("bio",            models.TextField(blank=True, null=True)),
                ("budget_min",     models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("budget_max",     models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("preferred_area", models.CharField(blank=True, max_length=200, null=True)),
                ("sleep_schedule", models.CharField(blank=True, max_length=20, null=True)),
                ("cleanliness",    models.CharField(blank=True, max_length=20, null=True)),
                ("noise_level",    models.CharField(blank=True, max_length=20, null=True)),
                ("smoking",        models.BooleanField(default=False)),
                ("pets",           models.BooleanField(default=False)),
                ("campus_id",      models.CharField(max_length=80)),
                ("active",         models.BooleanField(default=True)),
                ("created_at",     models.DateTimeField(auto_now_add=True)),
                ("updated_at",     models.DateTimeField(auto_now=True)),
                ("user",           models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="roommate_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "roommate_profiles"},
        ),
        migrations.CreateModel(
            name="HousingAlert",
            fields=[
                ("id",            models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("max_rent",      models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("min_bedrooms",  models.SmallIntegerField(blank=True, null=True)),
                ("location_name", models.CharField(blank=True, max_length=200, null=True)),
                ("radius_km",     models.SmallIntegerField(blank=True, null=True)),
                ("amenities",     models.JSONField(blank=True, default=list)),
                ("active",        models.BooleanField(default=True)),
                ("created_at",    models.DateTimeField(auto_now_add=True)),
                ("user",          models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="housing_alerts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "housing_alerts"},
        ),
        migrations.CreateModel(
            name="HousingSaved",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_by", to="housing.housinglisting")),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_housing", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "housing_saved"},
            bases=(models.Model,),
        ),
        migrations.AddConstraint(
            model_name="housingsaved",
            constraint=models.UniqueConstraint(fields=["user","listing"], name="unique_user_saved_housing"),
        ),
    ]
EOF

# ── events ─────────────────────────────────────────────────────────────────────
cat > apps/events/migrations/0001_initial.py << 'EOF'
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
EOF

# ── study ──────────────────────────────────────────────────────────────────────
cat > apps/study/migrations/0001_initial.py << 'EOF'
from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Tutor",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subjects",     models.JSONField(default=list)),
                ("hourly_rate",  models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("bio",          models.TextField(blank=True, null=True)),
                ("rating",       models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ("review_count", models.PositiveIntegerField(default=0)),
                ("available",    models.BooleanField(default=True)),
                ("campus_id",    models.CharField(max_length=80)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("user",         models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="tutor_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "tutors"},
        ),
        migrations.CreateModel(
            name="StudyBooking",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subject",      models.CharField(max_length=100)),
                ("scheduled_at", models.DateTimeField()),
                ("duration_min", models.PositiveIntegerField(default=60)),
                ("status",       models.CharField(choices=[("pending","Pending"),("confirmed","Confirmed"),("cancelled","Cancelled"),("completed","Completed")], default="pending", max_length=20)),
                ("notes",        models.TextField(blank=True, null=True)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("student",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_bookings", to=settings.AUTH_USER_MODEL)),
                ("tutor",        models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="bookings", to="study.tutor")),
            ],
            options={"db_table": "study_bookings", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyGroup",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name",         models.CharField(max_length=150)),
                ("subject",      models.CharField(max_length=100)),
                ("description",  models.TextField(blank=True, null=True)),
                ("max_members",  models.PositiveIntegerField(default=10)),
                ("member_count", models.PositiveIntegerField(default=1)),
                ("campus_id",    models.CharField(max_length=80)),
                ("active",       models.BooleanField(default=True)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("creator",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="created_groups", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_groups", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyGroupMember",
            fields=[
                ("id",        models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("group",     models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="memberships", to="study.studygroup")),
                ("user",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_groups_joined", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_group_members"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="StudyResource",
            fields=[
                ("id",             models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",          models.CharField(max_length=200)),
                ("subject",        models.CharField(max_length=100)),
                ("resource_type",  models.CharField(choices=[("pdf","PDF"),("doc","Doc"),("video","Video"),("link","Link"),("other","Other")], max_length=30)),
                ("file_url",       models.URLField(max_length=500)),
                ("download_count", models.PositiveIntegerField(default=0)),
                ("campus_id",      models.CharField(max_length=80)),
                ("created_at",     models.DateTimeField(auto_now_add=True)),
                ("uploader",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="uploaded_resources", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_resources", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyQuestion",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",        models.CharField(max_length=300)),
                ("body",         models.TextField()),
                ("subject",      models.CharField(blank=True, max_length=100, null=True)),
                ("tags",         models.JSONField(blank=True, default=list)),
                ("answer_count", models.PositiveIntegerField(default=0)),
                ("upvotes",      models.PositiveIntegerField(default=0)),
                ("campus_id",    models.CharField(max_length=80)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("author",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_questions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "study_questions", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudyAnswer",
            fields=[
                ("id",          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body",        models.TextField()),
                ("upvotes",     models.PositiveIntegerField(default=0)),
                ("is_accepted", models.BooleanField(default=False)),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
                ("author",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_answers", to=settings.AUTH_USER_MODEL)),
                ("question",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="answers", to="study.studyquestion")),
            ],
            options={"db_table": "study_answers", "ordering": ["-is_accepted","-upvotes","created_at"]},
        ),
        migrations.AddConstraint(
            model_name="studygroupmember",
            constraint=models.UniqueConstraint(fields=["group","user"], name="unique_group_member"),
        ),
    ]
EOF

echo ""
echo "✅ All 6 migration files fixed for Django 5."
echo "Now run: python3 manage.py migrate"