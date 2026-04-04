from rest_framework import serializers
from .models import (
    HousingAlert, HousingListing, HousingModuleSettings,
    RoommatePreference, RoommateProfile, LISTING_TAGS,
)

VALID_TAGS = [t[0] for t in LISTING_TAGS]


class HousingListingSerializer(serializers.ModelSerializer):
    landlordId    = serializers.UUIDField(source="landlord_id", read_only=True)
    rentPerMonth  = serializers.DecimalField(source="rent_per_month", max_digits=10, decimal_places=2)
    locationName  = serializers.CharField(source="location_name")
    imageUrls     = serializers.JSONField(source="image_urls")
    availableFrom = serializers.DateField(source="available_from", allow_null=True)
    createdAt     = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = HousingListing
        fields = [
            "id", "landlordId", "title", "description", "rentPerMonth",
            "locationName", "latitude", "longitude", "bedrooms", "bathrooms",
            "amenities", "tags", "imageUrls", "availableFrom", "status", "createdAt",
        ]


class CreateHousingListingSerializer(serializers.Serializer):
    title          = serializers.CharField(max_length=200)
    description    = serializers.CharField(required=False)
    rent_per_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    location_name  = serializers.CharField(max_length=200)
    latitude       = serializers.FloatField()
    longitude      = serializers.FloatField()
    bedrooms       = serializers.IntegerField(required=False, allow_null=True)
    bathrooms      = serializers.IntegerField(required=False, allow_null=True)
    amenities      = serializers.ListField(child=serializers.CharField(), default=list)
    tags           = serializers.ListField(
                         child=serializers.ChoiceField(choices=VALID_TAGS),
                         default=list,
                     )
    image_urls     = serializers.ListField(child=serializers.URLField(), default=list)
    available_from = serializers.DateField(required=False, allow_null=True)


class UpdateHousingListingSerializer(serializers.Serializer):
    title          = serializers.CharField(required=False)
    description    = serializers.CharField(required=False)
    rent_per_month = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    amenities      = serializers.ListField(child=serializers.CharField(), required=False)
    tags           = serializers.ListField(
                         child=serializers.ChoiceField(choices=VALID_TAGS),
                         required=False,
                     )
    image_urls     = serializers.ListField(child=serializers.URLField(), required=False)
    status         = serializers.ChoiceField(choices=["active", "rented", "removed"], required=False)


class RoommateProfileSerializer(serializers.ModelSerializer):
    userId        = serializers.UUIDField(source="user_id", read_only=True)
    budgetMin     = serializers.DecimalField(source="budget_min", max_digits=10, decimal_places=2, allow_null=True)
    budgetMax     = serializers.DecimalField(source="budget_max", max_digits=10, decimal_places=2, allow_null=True)
    preferredArea = serializers.CharField(source="preferred_area", allow_null=True)
    sleepSchedule = serializers.CharField(source="sleep_schedule", allow_null=True)
    noiseLevel    = serializers.CharField(source="noise_level", allow_null=True)
    createdAt     = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = RoommateProfile
        fields = [
            "id", "userId", "bio", "budgetMin", "budgetMax", "preferredArea",
            "sleepSchedule", "cleanliness", "noiseLevel", "smoking", "pets",
            "active", "createdAt",
        ]


class CreateRoommateProfileSerializer(serializers.Serializer):
    bio            = serializers.CharField(required=False, allow_blank=True)
    budget_min     = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    budget_max     = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    preferred_area = serializers.CharField(required=False, allow_blank=True)
    sleep_schedule = serializers.ChoiceField(choices=["early_bird", "night_owl", "flexible"], required=False)
    cleanliness    = serializers.ChoiceField(choices=["very_clean", "moderate", "relaxed"], required=False)
    noise_level    = serializers.ChoiceField(choices=["quiet", "moderate", "lively"], required=False)
    smoking        = serializers.BooleanField(default=False)
    pets           = serializers.BooleanField(default=False)


class RoommatePreferenceSerializer(serializers.ModelSerializer):
    userId           = serializers.UUIDField(source="user_id", read_only=True)
    budgetMin        = serializers.DecimalField(source="budget_min", max_digits=10, decimal_places=2, allow_null=True)
    budgetMax        = serializers.DecimalField(source="budget_max", max_digits=10, decimal_places=2, allow_null=True)
    preferredArea    = serializers.CharField(source="preferred_area", allow_null=True)
    genderPreference = serializers.CharField(source="gender_preference")
    sleepSchedule    = serializers.CharField(source="sleep_schedule", allow_null=True)
    noiseLevel       = serializers.CharField(source="noise_level", allow_null=True)
    createdAt        = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = RoommatePreference
        fields = [
            "id", "userId", "budgetMin", "budgetMax", "preferredArea",
            "genderPreference", "sleepSchedule", "cleanliness", "noiseLevel",
            "smoking", "pets", "active", "createdAt",
        ]


class CreateRoommatePreferenceSerializer(serializers.Serializer):
    budget_min        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    budget_max        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    preferred_area    = serializers.CharField(required=False, allow_blank=True)
    gender_preference = serializers.ChoiceField(choices=["male", "female", "any"], default="any")
    sleep_schedule    = serializers.ChoiceField(choices=["early_bird", "night_owl", "flexible"], required=False)
    cleanliness       = serializers.ChoiceField(choices=["very_clean", "moderate", "relaxed"], required=False)
    noise_level       = serializers.ChoiceField(choices=["quiet", "moderate", "lively"], required=False)
    smoking           = serializers.BooleanField(default=False)
    pets              = serializers.BooleanField(default=False)


class CreateAlertSerializer(serializers.Serializer):
    max_rent        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    min_bedrooms    = serializers.IntegerField(required=False, allow_null=True)
    location_name   = serializers.CharField(required=False, allow_blank=True)
    radius_km       = serializers.IntegerField(required=False, allow_null=True)
    amenities       = serializers.ListField(child=serializers.CharField(), default=list)
    notify_roommate = serializers.BooleanField(default=False)


class HousingModuleSettingsSerializer(serializers.ModelSerializer):
    updatedBy = serializers.CharField(source="updated_by", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model  = HousingModuleSettings
        fields = ["enabled", "updatedBy", "updatedAt"]