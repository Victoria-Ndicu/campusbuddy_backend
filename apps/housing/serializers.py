from rest_framework import serializers
from .models import HousingAlert, HousingListing, RoommateProfile


class HousingListingSerializer(serializers.ModelSerializer):
    landlordId    = serializers.UUIDField(source="landlord_id", read_only=True)
    rentPerMonth  = serializers.DecimalField(source="rent_per_month", max_digits=10, decimal_places=2)
    locationName  = serializers.CharField(source="location_name")
    imageUrls     = serializers.JSONField(source="image_urls")
    availableFrom = serializers.DateField(source="available_from", allow_null=True)
    campusId      = serializers.CharField(source="campus_id")
    createdAt     = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = HousingListing
        fields = [
            "id", "landlordId", "title", "description", "rentPerMonth",
            "locationName", "latitude", "longitude", "bedrooms", "bathrooms",
            "amenities", "imageUrls", "availableFrom", "status", "campusId", "createdAt",
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
    image_urls     = serializers.ListField(child=serializers.URLField(), default=list)
    available_from = serializers.DateField(required=False, allow_null=True)
    campus_id      = serializers.CharField(max_length=80)


class UpdateHousingListingSerializer(serializers.Serializer):
    title          = serializers.CharField(required=False)
    description    = serializers.CharField(required=False)
    rent_per_month = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    amenities      = serializers.ListField(child=serializers.CharField(), required=False)
    image_urls     = serializers.ListField(child=serializers.URLField(), required=False)
    status         = serializers.ChoiceField(choices=["active", "rented", "removed"], required=False)


class RoommateProfileSerializer(serializers.ModelSerializer):
    userId       = serializers.UUIDField(source="user_id", read_only=True)
    budgetMin    = serializers.DecimalField(source="budget_min", max_digits=10, decimal_places=2, allow_null=True)
    budgetMax    = serializers.DecimalField(source="budget_max", max_digits=10, decimal_places=2, allow_null=True)
    preferredArea = serializers.CharField(source="preferred_area", allow_null=True)
    sleepSchedule = serializers.CharField(source="sleep_schedule", allow_null=True)
    noiseLevel   = serializers.CharField(source="noise_level", allow_null=True)
    campusId     = serializers.CharField(source="campus_id")
    createdAt    = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = RoommateProfile
        fields = [
            "id", "userId", "bio", "budgetMin", "budgetMax", "preferredArea",
            "sleepSchedule", "cleanliness", "noiseLevel", "smoking", "pets",
            "campusId", "active", "createdAt",
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
    campus_id      = serializers.CharField(max_length=80)


class CreateAlertSerializer(serializers.Serializer):
    max_rent      = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    min_bedrooms  = serializers.IntegerField(required=False, allow_null=True)
    location_name = serializers.CharField(required=False, allow_blank=True)
    radius_km     = serializers.IntegerField(required=False, allow_null=True)
    amenities     = serializers.ListField(child=serializers.CharField(), default=list)