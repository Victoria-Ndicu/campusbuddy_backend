"""HousingHub service layer."""
from rest_framework import status
from core.exceptions import AppError
from core.services.storage_service import upload_file, validate_image
from .models import (
    HousingAlert, HousingListing, HousingModuleSettings,
    HousingSaved, RoommatePreference, RoommateProfile,
)


# ---------------------------------------------------------------------------
# Module guard
# ---------------------------------------------------------------------------

def check_module_enabled():
    if not HousingModuleSettings.get().enabled:
        raise AppError(status.HTTP_403_FORBIDDEN, "MODULE_DISABLED", "Housing module is currently disabled.")


# ---------------------------------------------------------------------------
# Module settings (admin)
# ---------------------------------------------------------------------------

def get_module_settings() -> dict:
    from .serializers import HousingModuleSettingsSerializer
    return {"success": True, "data": HousingModuleSettingsSerializer(HousingModuleSettings.get()).data}


def toggle_module(enabled: bool, user) -> dict:
    obj = HousingModuleSettings.get()
    obj.enabled = enabled
    obj.updated_by = str(user)
    obj.save()
    return {"success": True, "message": f"Housing module {'enabled' if enabled else 'disabled'}."}


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

def list_listings(filters: dict):
    check_module_enabled()
    qs = HousingListing.objects.filter(status="active")
    if filters.get("max_rent"):
        qs = qs.filter(rent_per_month__lte=filters["max_rent"])
    if filters.get("min_bedrooms"):
        qs = qs.filter(bedrooms__gte=filters["min_bedrooms"])
    if filters.get("search"):
        qs = qs.filter(title__icontains=filters["search"])
    if filters.get("tags"):
        for tag in filters["tags"]:
            qs = qs.filter(tags__contains=tag)
    return qs


def get_listing(listing_id: str) -> dict:
    check_module_enabled()
    listing = _get_or_404(listing_id)
    from .serializers import HousingListingSerializer
    return {"success": True, "data": HousingListingSerializer(listing).data}


def create_listing(data: dict, user) -> dict:
    check_module_enabled()
    listing = HousingListing.objects.create(landlord=user, **{
        k: v for k, v in data.items() if v is not None
    })
    _fire_alerts(listing)
    from .serializers import HousingListingSerializer
    return {"success": True, "data": HousingListingSerializer(listing).data}


def update_listing(listing_id: str, data: dict, user) -> dict:
    check_module_enabled()
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user)
    for field, value in data.items():
        if value is not None:
            setattr(listing, field, value)
    listing.save()
    from .serializers import HousingListingSerializer
    return {"success": True, "data": HousingListingSerializer(listing).data}


def delete_listing(listing_id: str, user) -> dict:
    check_module_enabled()
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user)
    listing.status = "removed"
    listing.save(update_fields=["status"])
    return {"success": True, "message": "Listing removed."}


def toggle_save(listing_id: str, user) -> dict:
    check_module_enabled()
    _get_or_404(listing_id)
    saved, created = HousingSaved.objects.get_or_create(user=user, listing_id=listing_id)
    if not created:
        saved.delete()
        return {"success": True, "saved": False}
    return {"success": True, "saved": True}


def upload_image(file, user) -> dict:
    check_module_enabled()
    validate_image(file)
    url = upload_file(file, folder="housing", user_id=str(user.id))
    return {"success": True, "data": {"url": url}}


# ---------------------------------------------------------------------------
# Roommate profiles
# ---------------------------------------------------------------------------

def get_roommate_profiles(current_user):
    check_module_enabled()
    qs = RoommateProfile.objects.filter(active=True).exclude(user=current_user)

    try:
        my_pref = current_user.roommate_preference
    except RoommatePreference.DoesNotExist:
        my_pref = None

    profiles = list(qs.select_related("user"))

    def _score(profile):
        score = 0
        if my_pref:
            # Budget overlap — highest weight
            if (my_pref.budget_min and my_pref.budget_max
                    and profile.budget_min and profile.budget_max):
                overlap = (min(float(my_pref.budget_max), float(profile.budget_max))
                           - max(float(my_pref.budget_min), float(profile.budget_min)))
                if overlap >= 0:
                    score += 40
            # Location match — high weight
            if (my_pref.preferred_area and profile.preferred_area
                    and my_pref.preferred_area.lower() == profile.preferred_area.lower()):
                score += 30
            # Lifestyle fields
            for field in ["sleep_schedule", "cleanliness", "noise_level"]:
                pref_val = getattr(my_pref, field)
                prof_val = getattr(profile, field)
                if pref_val and prof_val and pref_val == prof_val:
                    score += 8
            if my_pref.smoking == profile.smoking:
                score += 7
            if my_pref.pets == profile.pets:
                score += 7
            # Gender preference
            gender_preference = getattr(my_pref, "gender_preference", "any")
            profile_gender = getattr(profile.user, "gender", None)
            if gender_preference != "any" and profile_gender:
                if gender_preference == profile_gender:
                    score += 20
                else:
                    score -= 20
        return score

    profiles.sort(key=_score, reverse=True)
    return profiles


def upsert_roommate_profile(data: dict, user) -> dict:
    check_module_enabled()
    profile, _ = RoommateProfile.objects.update_or_create(
        user=user,
        defaults={k: v for k, v in data.items() if v is not None},
    )
    from .serializers import RoommateProfileSerializer
    return {"success": True, "data": RoommateProfileSerializer(profile).data}


def upsert_roommate_preference(data: dict, user) -> dict:
    check_module_enabled()
    pref, _ = RoommatePreference.objects.update_or_create(
        user=user,
        defaults={k: v for k, v in data.items() if v is not None},
    )
    from .serializers import RoommatePreferenceSerializer
    return {"success": True, "data": RoommatePreferenceSerializer(pref).data}


def get_roommate_preference(user) -> dict:
    check_module_enabled()
    try:
        pref = user.roommate_preference
    except RoommatePreference.DoesNotExist:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "No roommate preference set yet.")
    from .serializers import RoommatePreferenceSerializer
    return {"success": True, "data": RoommatePreferenceSerializer(pref).data}


def compute_compatibility(me: RoommateProfile, other: RoommateProfile) -> int:
    score = 100
    for field in ["sleep_schedule", "cleanliness", "noise_level"]:
        if getattr(me, field) and getattr(other, field) and getattr(me, field) != getattr(other, field):
            score -= 15
    if me.budget_min and me.budget_max and other.budget_min and other.budget_max:
        overlap = (min(float(me.budget_max), float(other.budget_max))
                   - max(float(me.budget_min), float(other.budget_min)))
        if overlap < 0:
            score -= 10
    if me.smoking != other.smoking:
        score -= 10
    if me.pets != other.pets:
        score -= 5
    return max(0, score)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def create_alert(data: dict, user) -> dict:
    check_module_enabled()
    HousingAlert.objects.create(user=user, **data)
    return {"success": True, "message": "Alert created."}


def list_alerts(user):
    check_module_enabled()
    return HousingAlert.objects.filter(user=user, active=True)


def delete_alert(alert_id: str, user) -> dict:
    check_module_enabled()
    updated = HousingAlert.objects.filter(pk=alert_id, user=user).update(active=False)
    if not updated:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Alert not found.")
    return {"success": True, "message": "Alert deleted."}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fire_alerts(listing: HousingListing) -> None:
    alerts = HousingAlert.objects.filter(active=True)
    for alert in alerts:
        if alert.max_rent and float(listing.rent_per_month) > float(alert.max_rent):
            continue
        if alert.min_bedrooms and (not listing.bedrooms or listing.bedrooms < alert.min_bedrooms):
            continue
        from apps.housing.tasks import notify_housing_alert
        notify_housing_alert.delay(
            str(alert.user_id), str(listing.id),
            listing.title, float(listing.rent_per_month),
        )


def _fire_roommate_alerts(new_profile: RoommateProfile) -> None:
    """Called when a new RoommateProfile is created/activated. Notifies users
    whose alert has notify_roommate=True and whose preference matches this profile."""
    alerts = HousingAlert.objects.filter(active=True, notify_roommate=True)
    for alert in alerts:
        if alert.user_id == new_profile.user_id:
            continue
        try:
            pref = alert.user.roommate_preference
        except RoommatePreference.DoesNotExist:
            continue
        # Must have budget overlap and location match to qualify as a match
        budget_ok = True
        if (pref.budget_min and pref.budget_max
                and new_profile.budget_min and new_profile.budget_max):
            overlap = (min(float(pref.budget_max), float(new_profile.budget_max))
                       - max(float(pref.budget_min), float(new_profile.budget_min)))
            budget_ok = overlap >= 0
        location_ok = (
            not pref.preferred_area
            or not new_profile.preferred_area
            or pref.preferred_area.lower() == new_profile.preferred_area.lower()
        )
        if not (budget_ok and location_ok):
            continue
        from apps.housing.tasks import notify_roommate_found
        notify_roommate_found.delay(str(alert.user_id), str(new_profile.user_id))


def _get_or_404(listing_id: str) -> HousingListing:
    listing = HousingListing.objects.filter(pk=listing_id).first()
    if not listing:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Housing listing not found.")
    return listing


def _assert_owner(listing: HousingListing, user) -> None:
    if listing.landlord != user and getattr(user, "role", "") != "admin":
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "You do not own this listing.")