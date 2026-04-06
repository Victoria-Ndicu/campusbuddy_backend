import uuid
from django.conf import settings
from django.db import models


LISTING_TAGS = [
    ("apartment", "Apartment"),
    ("single_room", "Single room"),
    ("shared_room", "Shared room"),
    ("bedsitter", "Bedsitter"),
    ("hostel", "Hostel"),
]


class HousingModuleSettings(models.Model):
    enabled    = models.BooleanField(default=True)
    updated_by = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_module_settings"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HousingListing(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("rented", "Rented"), ("removed", "Removed")]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    landlord       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="housing_listings")
    title          = models.CharField(max_length=200)
    description    = models.TextField(blank=True, null=True)
    rent_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    location_name  = models.CharField(max_length=200)
    latitude       = models.DecimalField(max_digits=10, decimal_places=7)
    longitude      = models.DecimalField(max_digits=10, decimal_places=7)
    bedrooms       = models.SmallIntegerField(null=True, blank=True)
    bathrooms      = models.SmallIntegerField(null=True, blank=True)
    amenities      = models.JSONField(default=list, blank=True)
    tags           = models.JSONField(default=list, blank=True)
    image_urls     = models.JSONField(default=list, blank=True)
    available_from = models.DateField(null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_listings"
        ordering = ["-created_at"]

    @property
    def owner(self):
        return self.landlord


class RoommateProfile(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roommate_profile")
    bio             = models.TextField(blank=True, null=True)
    budget_min      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # preferred_area kept for backward compat and scoring (first item of preferred_areas)
    preferred_area  = models.CharField(max_length=200, blank=True, null=True)
    # preferred_areas stores the full list Flutter sends as preferred_locations
    preferred_areas = models.JSONField(default=list, blank=True)
    sleep_schedule  = models.CharField(max_length=20, blank=True, null=True)
    cleanliness     = models.CharField(max_length=20, blank=True, null=True)
    noise_level     = models.CharField(max_length=20, blank=True, null=True)
    smoking         = models.BooleanField(default=False)
    pets            = models.BooleanField(default=False)
    active          = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roommate_profiles"


class RoommatePreference(models.Model):
    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("any", "Any")]

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user              = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roommate_preference")
    budget_min        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_area    = models.CharField(max_length=200, blank=True, null=True)
    preferred_areas   = models.JSONField(default=list, blank=True)
    gender_preference = models.CharField(max_length=10, choices=GENDER_CHOICES, default="any")
    sleep_schedule    = models.CharField(max_length=20, blank=True, null=True)
    cleanliness       = models.CharField(max_length=20, blank=True, null=True)
    noise_level       = models.CharField(max_length=20, blank=True, null=True)
    smoking           = models.BooleanField(default=False)
    pets              = models.BooleanField(default=False)
    active            = models.BooleanField(default=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roommate_preferences"


class HousingAlert(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="housing_alerts")
    max_rent        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_bedrooms    = models.SmallIntegerField(null=True, blank=True)
    location_name   = models.CharField(max_length=200, blank=True, null=True)
    radius_km       = models.SmallIntegerField(null=True, blank=True)
    amenities       = models.JSONField(default=list, blank=True)
    notify_roommate = models.BooleanField(default=False)
    active          = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "housing_alerts"


class HousingSaved(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_housing")
    listing    = models.ForeignKey(HousingListing, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "housing_saved"
        unique_together = [["user", "listing"]]


class AlertNotification(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_notifications")
    listing       = models.ForeignKey(HousingListing, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications")
    listing_title = models.CharField(max_length=200, blank=True)
    message       = models.TextField()
    emoji         = models.CharField(max_length=10, blank=True, default="🔔")
    is_read       = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "alert_notifications"
        ordering = ["-created_at"]