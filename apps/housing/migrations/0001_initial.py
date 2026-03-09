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
