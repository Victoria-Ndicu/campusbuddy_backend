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

ALERT_RULE_TYPES = [
    ("area",              "Area Alert"),
    ("price_drop",        "Price Alert"),
    ("listing_available", "Availability Alert"),
    ("new_listing",       "New Listing Alert"),
]


# ---------------------------------------------------------------------------
# Global module settings  (admin-level kill switch)
# ---------------------------------------------------------------------------

class HousingModuleSettings(models.Model):
    """Single-row global toggle — admin can disable the entire housing module."""
    enabled    = models.BooleanField(default=True)
    updated_by = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_module_settings"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ---------------------------------------------------------------------------
# Per-user housing module preference
# ---------------------------------------------------------------------------

class UserHousingPreference(models.Model):
    """
    Stores whether an individual user has opted IN to the housing module.

    Rules:
    - Default is False — user must explicitly turn it on.
    - Stored in DB so it survives sign-out / sign-in cycles.
    - Only the user's own PATCH to /api/v1/user/preferences/ can change it.
    - The backend never flips this automatically.
    """
    user                   = models.OneToOneField(
                                 settings.AUTH_USER_MODEL,
                                 on_delete=models.CASCADE,
                                 related_name="housing_preference",
                             )
    housing_module_enabled = models.BooleanField(default=False)
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_housing_preferences"

    @classmethod
    def for_user(cls, user):
        """Return (or create with default=False) the preference row for this user."""
        obj, _ = cls.objects.get_or_create(user=user)
        return obj


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Roommate models
# ---------------------------------------------------------------------------

class RoommateProfile(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roommate_profile")
    bio             = models.TextField(blank=True, null=True)
    budget_min      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_area  = models.CharField(max_length=200, blank=True, null=True)
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


# ---------------------------------------------------------------------------
# Housing alerts  (per-user alert rules)
# ---------------------------------------------------------------------------

class HousingAlert(models.Model):
    """
    A user-defined alert rule. Fields aligned with Flutter's _AlertRule model.
    Legacy fields kept for backward compat with _fire_alerts service logic.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="housing_alerts")

    # Flutter-aligned fields
    rule_type      = models.CharField(max_length=30, choices=ALERT_RULE_TYPES, default="new_listing")
    label          = models.CharField(max_length=200, blank=True)
    area           = models.CharField(max_length=200, blank=True, null=True)
    max_price      = models.IntegerField(null=True, blank=True)
    property_types = models.JSONField(default=list, blank=True)
    is_active      = models.BooleanField(default=True)

    # Legacy fields — kept so _fire_alerts() still works
    max_rent        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_bedrooms    = models.SmallIntegerField(null=True, blank=True)
    location_name   = models.CharField(max_length=200, blank=True, null=True)
    radius_km       = models.SmallIntegerField(null=True, blank=True)
    amenities       = models.JSONField(default=list, blank=True)
    notify_roommate = models.BooleanField(default=False)
    active          = models.BooleanField(default=True)   # mirrors is_active

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_alerts"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Keep legacy fields in sync
        self.active   = self.is_active
        if self.max_price and not self.max_rent:
            self.max_rent = self.max_price
        if self.area and not self.location_name:
            self.location_name = self.area
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Saved listings
# ---------------------------------------------------------------------------

class HousingSaved(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_housing")
    listing    = models.ForeignKey(HousingListing, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "housing_saved"
        unique_together = [["user", "listing"]]


# ---------------------------------------------------------------------------
# Alert notifications  (inbox items)
# ---------------------------------------------------------------------------

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