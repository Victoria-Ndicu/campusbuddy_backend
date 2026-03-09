"""HousingHub service layer."""
from rest_framework import status
from core.exceptions import AppError
from core.services.storage_service import upload_file, validate_image
from .models import HousingAlert, HousingListing, HousingSaved, RoommateProfile


def list_listings(filters: dict):
    qs = HousingListing.objects.filter(status="active")
    if filters.get("campus_id"):
        qs = qs.filter(campus_id=filters["campus_id"])
    if filters.get("max_rent"):
        qs = qs.filter(rent_per_month__lte=filters["max_rent"])
    if filters.get("min_bedrooms"):
        qs = qs.filter(bedrooms__gte=filters["min_bedrooms"])
    if filters.get("search"):
        qs = qs.filter(title__icontains=filters["search"])
    return qs


def get_listing(listing_id: str) -> dict:
    listing = _get_or_404(listing_id)
    from .serializers import HousingListingSerializer
    return {"success": True, "data": HousingListingSerializer(listing).data}


def create_listing(data: dict, user) -> dict:
    listing = HousingListing.objects.create(landlord=user, **{
        k: v for k, v in data.items() if v is not None
    })
    # Fire housing alerts
    _fire_alerts(listing)
    from .serializers import HousingListingSerializer
    return {"success": True, "data": HousingListingSerializer(listing).data}


def update_listing(listing_id: str, data: dict, user) -> dict:
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user)
    for field, value in data.items():
        if value is not None:
            setattr(listing, field, value)
    listing.save()
    from .serializers import HousingListingSerializer
    return {"success": True, "data": HousingListingSerializer(listing).data}


def delete_listing(listing_id: str, user) -> dict:
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user)
    listing.status = "removed"
    listing.save(update_fields=["status"])
    return {"success": True, "message": "Listing removed."}


def toggle_save(listing_id: str, user) -> dict:
    _get_or_404(listing_id)
    saved, created = HousingSaved.objects.get_or_create(user=user, listing_id=listing_id)
    if not created:
        saved.delete()
        return {"success": True, "saved": False}
    return {"success": True, "saved": True}


def upload_image(file, user) -> dict:
    validate_image(file)
    url = upload_file(file, folder="housing", user_id=str(user.id))
    return {"success": True, "data": {"url": url}}


def get_roommate_profiles(campus_id: str | None, current_user):
    qs = RoommateProfile.objects.filter(active=True)
    if campus_id:
        qs = qs.filter(campus_id=campus_id)
    return qs, current_user


def upsert_roommate_profile(data: dict, user) -> dict:
    profile, _ = RoommateProfile.objects.update_or_create(
        user=user,
        defaults={k: v for k, v in data.items() if v is not None},
    )
    from .serializers import RoommateProfileSerializer
    return {"success": True, "data": RoommateProfileSerializer(profile).data}


def compute_compatibility(me: RoommateProfile, other: RoommateProfile) -> int:
    score = 100
    for field in ["sleep_schedule", "cleanliness", "noise_level"]:
        if getattr(me, field) and getattr(other, field) and getattr(me, field) != getattr(other, field):
            score -= 15
    if me.budget_min and me.budget_max and other.budget_min and other.budget_max:
        overlap = min(float(me.budget_max), float(other.budget_max)) - max(float(me.budget_min), float(other.budget_min))
        if overlap < 0:
            score -= 10
    if me.smoking != other.smoking:
        score -= 10
    if me.pets != other.pets:
        score -= 5
    return max(0, score)


def create_alert(data: dict, user) -> dict:
    HousingAlert.objects.create(user=user, **data)
    return {"success": True, "message": "Alert created."}


def list_alerts(user):
    return HousingAlert.objects.filter(user=user, active=True)


def delete_alert(alert_id: str, user) -> dict:
    updated = HousingAlert.objects.filter(pk=alert_id, user=user).update(active=False)
    if not updated:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Alert not found.")
    return {"success": True, "message": "Alert deleted."}


def _fire_alerts(listing: HousingListing) -> None:
    alerts = HousingAlert.objects.filter(active=True)
    for alert in alerts:
        if alert.max_rent and float(listing.rent_per_month) > float(alert.max_rent):
            continue
        if alert.min_bedrooms and (not listing.bedrooms or listing.bedrooms < alert.min_bedrooms):
            continue
        from apps.housing.tasks import notify_housing_alert
        notify_housing_alert.delay(str(alert.user_id), str(listing.id), listing.title, float(listing.rent_per_month))


def _get_or_404(listing_id: str) -> HousingListing:
    listing = HousingListing.objects.filter(pk=listing_id).first()
    if not listing:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Housing listing not found.")
    return listing


def _assert_owner(listing: HousingListing, user) -> None:
    if listing.landlord != user and getattr(user, "role", "") != "admin":
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "You do not own this listing.")