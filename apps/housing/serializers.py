from rest_framework import serializers
from .models import (
    HousingAlert, HousingListing, HousingModuleSettings,
    RoommatePreference, RoommateProfile, LISTING_TAGS,
)

VALID_TAGS = [t[0] for t in LISTING_TAGS]


# ---------------------------------------------------------------------------
# Housing listing serializers  (unchanged from original)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Roommate profile serializer  — shaped to match Flutter's _Roommate.fromJson
# ---------------------------------------------------------------------------

class RoommateProfileSerializer(serializers.ModelSerializer):
    """
    Output keys match exactly what Flutter reads:
        id, name, course, year, preferred_location,
        match_percent, lifestyle_prefs, budget_range, about
    Additional raw fields are included for the detail screen.
    """
    userId             = serializers.UUIDField(source="user_id", read_only=True)

    # Flutter _Roommate.fromJson reads these top-level keys
    name               = serializers.SerializerMethodField()
    course             = serializers.SerializerMethodField()
    year               = serializers.SerializerMethodField()
    preferred_location = serializers.SerializerMethodField()   # singular display string
    lifestyle_prefs    = serializers.SerializerMethodField()   # list of chip labels
    budget_range       = serializers.SerializerMethodField()   # "KES 5,000 – 15,000"
    about              = serializers.CharField(source="bio", allow_null=True, read_only=True)
    # match_percent is injected by the view after scoring; default 0 here
    match_percent      = serializers.IntegerField(default=0, read_only=True)

    # Raw fields kept for detail screen
    budgetMin          = serializers.DecimalField(source="budget_min", max_digits=10, decimal_places=2, allow_null=True)
    budgetMax          = serializers.DecimalField(source="budget_max", max_digits=10, decimal_places=2, allow_null=True)
    preferredAreas     = serializers.JSONField(source="preferred_areas", read_only=True)
    sleepSchedule      = serializers.CharField(source="sleep_schedule", allow_null=True)
    noiseLevel         = serializers.CharField(source="noise_level", allow_null=True)
    createdAt          = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = RoommateProfile
        fields = [
            "id", "userId",
            # Flutter-facing display fields
            "name", "course", "year", "preferred_location",
            "lifestyle_prefs", "budget_range", "about", "match_percent",
            # Raw fields for detail screen
            "budgetMin", "budgetMax", "preferredAreas",
            "sleepSchedule", "cleanliness", "noiseLevel",
            "smoking", "pets", "active", "createdAt",
        ]

    def get_name(self, obj):
        user = obj.user
        full = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        return full or getattr(user, 'username', str(user))

    def get_course(self, obj):
        # Adapt 'course' / 'program' to whatever field your user model uses
        return (
            getattr(obj.user, 'course', None)
            or getattr(obj.user, 'program', None)
            or ''
        )

    def get_year(self, obj):
        year = getattr(obj.user, 'year_of_study', None)
        if year:
            return f"Year {year} student"
        return ''

    def get_preferred_location(self, obj):
        # Return first area in the list, fall back to the legacy single field
        if obj.preferred_areas:
            return obj.preferred_areas[0]
        return obj.preferred_area or ''

    def get_lifestyle_prefs(self, obj):
        """Human-readable chip labels Flutter renders in the card."""
        prefs = []
        sleep_labels = {
            'early_bird': '🌅 Early bird',
            'night_owl':  '🌙 Night owl',
            'flexible':   '⏰ Flexible sleep',
        }
        clean_labels = {
            'very_clean': '🧹 Very tidy',
            'moderate':   '🏠 Moderate',
            'relaxed':    '😌 Relaxed',
        }
        noise_labels = {
            'quiet':    '🤫 Quiet',
            'moderate': '🎵 Moderate',
            'lively':   '🎉 Social',
        }
        for val, label in [(obj.sleep_schedule, sleep_labels),
                           (obj.cleanliness,    clean_labels),
                           (obj.noise_level,    noise_labels)]:
            if val and val in label:
                prefs.append(label[val])
        if not obj.smoking:
            prefs.append('🚭 Non-smoker')
        if obj.pets:
            prefs.append('🐾 Pets ok')
        return prefs

    def get_budget_range(self, obj):
        if obj.budget_min and obj.budget_max:
            return f"KES {int(obj.budget_min):,} – {int(obj.budget_max):,}"
        if obj.budget_max:
            return f"Up to KES {int(obj.budget_max):,}"
        return ''


# ---------------------------------------------------------------------------
# Create / update roommate profile  — accepts Flutter's field names
# ---------------------------------------------------------------------------

# Flutter's HHRoommatePrefsScreen POSTs:
#   sleep_schedule, cleanliness, noise_level,
#   no_smoking (bool), pets_ok (bool),
#   budget_max, preferred_locations (list)

_SLEEP_MAP = {'Early bird': 'early_bird', 'Night owl': 'night_owl', 'Flexible': 'flexible'}
_CLEAN_MAP = {'Very tidy': 'very_clean', 'Relaxed': 'relaxed', 'Moderate': 'moderate'}
_NOISE_MAP = {'Quiet': 'quiet', 'Moderate': 'moderate', 'Social': 'lively'}


class CreateRoommateProfileSerializer(serializers.Serializer):
    bio                 = serializers.CharField(required=False, allow_blank=True)
    budget_min          = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    budget_max          = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    # Flutter sends preferred_locations as a list e.g. ["Westlands", "CBD"]
    preferred_locations = serializers.ListField(
                              child=serializers.CharField(),
                              required=False,
                              default=list,
                          )
    sleep_schedule      = serializers.ChoiceField(
                              choices=["early_bird", "night_owl", "flexible",
                                       "Early bird", "Night owl", "Flexible"],
                              required=False,
                          )
    cleanliness         = serializers.ChoiceField(
                              choices=["very_clean", "moderate", "relaxed",
                                       "Very tidy", "Moderate", "Relaxed"],
                              required=False,
                          )
    noise_level         = serializers.ChoiceField(
                              choices=["quiet", "moderate", "lively",
                                       "Quiet", "Moderate", "Social"],
                              required=False,
                          )
    # Flutter sends no_smoking (inverted) and pets_ok — also accept direct DB names
    no_smoking          = serializers.BooleanField(required=False)
    pets_ok             = serializers.BooleanField(required=False)
    smoking             = serializers.BooleanField(required=False, default=False)
    pets                = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        # Normalise display values → DB values
        if 'sleep_schedule' in data:
            data['sleep_schedule'] = _SLEEP_MAP.get(data['sleep_schedule'], data['sleep_schedule'])
        if 'cleanliness' in data:
            data['cleanliness'] = _CLEAN_MAP.get(data['cleanliness'], data['cleanliness'])
        if 'noise_level' in data:
            data['noise_level'] = _NOISE_MAP.get(data['noise_level'], data['noise_level'])

        # no_smoking=True  → smoking=False  (non-smoker preferred)
        # no_smoking=False → smoking=True
        if 'no_smoking' in data:
            data['smoking'] = not data.pop('no_smoking')

        # pets_ok → pets
        if 'pets_ok' in data:
            data['pets'] = data.pop('pets_ok')

        # Convert list → preferred_areas + preferred_area (first item)
        locs = data.pop('preferred_locations', [])
        if locs:
            data['preferred_areas'] = locs
            data['preferred_area']  = locs[0]

        return data


# ---------------------------------------------------------------------------
# Roommate preference serializers
# ---------------------------------------------------------------------------

class RoommatePreferenceSerializer(serializers.ModelSerializer):
    userId           = serializers.UUIDField(source="user_id", read_only=True)
    budgetMin        = serializers.DecimalField(source="budget_min", max_digits=10, decimal_places=2, allow_null=True)
    budgetMax        = serializers.DecimalField(source="budget_max", max_digits=10, decimal_places=2, allow_null=True)
    preferredArea    = serializers.CharField(source="preferred_area", allow_null=True)
    preferredAreas   = serializers.JSONField(source="preferred_areas")
    genderPreference = serializers.CharField(source="gender_preference")
    sleepSchedule    = serializers.CharField(source="sleep_schedule", allow_null=True)
    noiseLevel       = serializers.CharField(source="noise_level", allow_null=True)
    createdAt        = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = RoommatePreference
        fields = [
            "id", "userId", "budgetMin", "budgetMax",
            "preferredArea", "preferredAreas",
            "genderPreference", "sleepSchedule", "cleanliness", "noiseLevel",
            "smoking", "pets", "active", "createdAt",
        ]


class CreateRoommatePreferenceSerializer(serializers.Serializer):
    budget_min          = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    budget_max          = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    preferred_locations = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    preferred_area      = serializers.CharField(required=False, allow_blank=True)
    gender_preference   = serializers.ChoiceField(choices=["male", "female", "any"], default="any")
    sleep_schedule      = serializers.ChoiceField(
                              choices=["early_bird", "night_owl", "flexible",
                                       "Early bird", "Night owl", "Flexible"],
                              required=False,
                          )
    cleanliness         = serializers.ChoiceField(
                              choices=["very_clean", "moderate", "relaxed",
                                       "Very tidy", "Moderate", "Relaxed"],
                              required=False,
                          )
    noise_level         = serializers.ChoiceField(
                              choices=["quiet", "moderate", "lively",
                                       "Quiet", "Moderate", "Social"],
                              required=False,
                          )
    no_smoking          = serializers.BooleanField(required=False)
    pets_ok             = serializers.BooleanField(required=False)
    smoking             = serializers.BooleanField(required=False, default=False)
    pets                = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        if 'sleep_schedule' in data:
            data['sleep_schedule'] = _SLEEP_MAP.get(data['sleep_schedule'], data['sleep_schedule'])
        if 'cleanliness' in data:
            data['cleanliness'] = _CLEAN_MAP.get(data['cleanliness'], data['cleanliness'])
        if 'noise_level' in data:
            data['noise_level'] = _NOISE_MAP.get(data['noise_level'], data['noise_level'])
        if 'no_smoking' in data:
            data['smoking'] = not data.pop('no_smoking')
        if 'pets_ok' in data:
            data['pets'] = data.pop('pets_ok')
        locs = data.pop('preferred_locations', [])
        if locs:
            data['preferred_areas'] = locs
            data['preferred_area']  = locs[0]
        return data


# ---------------------------------------------------------------------------
# Alert serializers  (unchanged)
# ---------------------------------------------------------------------------

class CreateAlertSerializer(serializers.Serializer):
    max_rent        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    min_bedrooms    = serializers.IntegerField(required=False, allow_null=True)
    location_name   = serializers.CharField(required=False, allow_blank=True)
    radius_km       = serializers.IntegerField(required=False, allow_null=True)
    amenities       = serializers.ListField(child=serializers.CharField(), default=list)
    notify_roommate = serializers.BooleanField(default=False)


# ---------------------------------------------------------------------------
# Module settings serializer  (unchanged)
# ---------------------------------------------------------------------------

class HousingModuleSettingsSerializer(serializers.ModelSerializer):
    updatedBy = serializers.CharField(source="updated_by", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model  = HousingModuleSettings
        fields = ["enabled", "updatedBy", "updatedAt"]