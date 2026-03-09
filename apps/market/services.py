"""CampusMarket service layer."""
from django.db.models import Avg
from rest_framework import status

from core.exceptions import AppError
from core.services.storage_service import upload_file, validate_image

from .models import (
    MarketDonationClaim, MarketListing, MarketMessage,
    MarketReview, MarketSavedListing,
)
from .serializers import MarketListingSerializer, MessageSerializer


def list_listings(filters: dict, user) -> dict:
    qs = MarketListing.objects.filter(status=filters.get("status", "active"))
    if filters.get("campus_id"):
        qs = qs.filter(campus_id=filters["campus_id"])
    if filters.get("category"):
        qs = qs.filter(category=filters["category"])
    if filters.get("listing_type"):
        qs = qs.filter(listing_type=filters["listing_type"])
    if filters.get("search"):
        qs = qs.filter(title__icontains=filters["search"])
    return qs


def get_listing(listing_id: str, user) -> dict:
    listing = _get_or_404(listing_id)
    MarketListing.objects.filter(pk=listing_id).update(view_count=listing.view_count + 1)
    listing.refresh_from_db()
    return {"success": True, "data": MarketListingSerializer(listing).data}


def create_listing(data: dict, user) -> dict:
    listing = MarketListing.objects.create(
        seller=user,
        title=data["title"],
        description=data.get("description", ""),
        price=data.get("price"),
        category=data["category"],
        condition=data.get("condition"),
        campus_id=data["campus_id"],
        listing_type=data.get("listing_type", "sale"),
        image_urls=data.get("image_urls", []),
    )
    return {"success": True, "data": MarketListingSerializer(listing).data}


def update_listing(listing_id: str, data: dict, user) -> dict:
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user)
    for field, value in data.items():
        if value is not None:
            setattr(listing, field, value)
    listing.save()
    return {"success": True, "data": MarketListingSerializer(listing).data}


def delete_listing(listing_id: str, user) -> dict:
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user, allow_admin=True)
    listing.status = "removed"
    listing.save(update_fields=["status"])
    return {"success": True, "message": "Listing removed."}


def upload_image(file, user) -> dict:
    validate_image(file)
    url = upload_file(file, folder="listings", user_id=str(user.id))
    return {"success": True, "data": {"url": url}}


def claim_donation(listing_id: str, message: str, user) -> dict:
    listing = _get_or_404(listing_id)
    if listing.listing_type != "donation" or listing.status != "active":
        raise AppError(status.HTTP_400_BAD_REQUEST, "NOT_DONATION", "This is not an active donation listing.")
    if listing.seller == user:
        raise AppError(status.HTTP_400_BAD_REQUEST, "OWN_LISTING", "You cannot claim your own donation.")
    if MarketDonationClaim.objects.filter(listing=listing, claimant=user).exists():
        raise AppError(status.HTTP_409_CONFLICT, "ALREADY_CLAIMED", "You have already claimed this item.")

    MarketDonationClaim.objects.create(listing=listing, claimant=user, message=message)

    from apps.market.tasks import notify_donation_claim
    notify_donation_claim.delay(str(listing.seller_id), str(listing.id), listing.title)

    return {"success": True, "message": "Claim submitted."}


def update_claim(listing_id: str, claim_id: str, new_status: str, user) -> dict:
    listing = _get_or_404(listing_id)
    _assert_owner(listing, user)
    claim = MarketDonationClaim.objects.filter(pk=claim_id, listing=listing).first()
    if not claim:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Claim not found.")
    claim.status = new_status
    claim.save(update_fields=["status"])
    if new_status == "confirmed":
        listing.status = "donated"
        listing.save(update_fields=["status"])
    return {"success": True, "message": f"Claim {new_status}."}


def send_message(data: dict, user) -> dict:
    from apps.authentication.models import User
    listing = _get_or_404(str(data["listing_id"]))
    try:
        receiver = User.objects.get(pk=data["receiver_id"])
    except User.DoesNotExist:
        raise AppError(status.HTTP_404_NOT_FOUND, "RECEIVER_NOT_FOUND", "Recipient not found.")

    msg = MarketMessage.objects.create(
        listing=listing,
        sender=user,
        receiver=receiver,
        body=data["body"],
        channel=data.get("channel", "in_app"),
    )

    from apps.market.tasks import notify_new_message
    notify_new_message.delay(str(receiver.id), str(listing.id), listing.title, data["body"][:100])

    if data.get("channel") == "email":
        from core.services.email_service import send_market_message_email
        send_market_message_email(
            to=receiver.email,
            sender_name=user.full_name or user.email,
            listing_title=listing.title,
            message_body=data["body"],
        )

    return {"success": True, "message": "Message sent.", "data": MessageSerializer(msg).data}


def get_messages(listing_id: str, user) -> list:
    listing = _get_or_404(listing_id)
    return MarketMessage.objects.filter(
        listing=listing
    ).filter(
        sender=user
    ) | MarketMessage.objects.filter(
        listing=listing, receiver=user
    )


def toggle_save(listing_id: str, user) -> dict:
    _get_or_404(listing_id)
    saved, created = MarketSavedListing.objects.get_or_create(user=user, listing_id=listing_id)
    if not created:
        saved.delete()
        return {"success": True, "saved": False}
    return {"success": True, "saved": True}


def get_saved_listings(user):
    return MarketListing.objects.filter(
        saved_by__user=user
    ).select_related("seller")


def create_review(data: dict, user) -> dict:
    listing = _get_or_404(str(data["listing_id"]))
    if listing.status not in ("sold", "donated"):
        raise AppError(status.HTTP_403_FORBIDDEN, "LISTING_ACTIVE", "Reviews can only be left after a transaction completes.")
    if MarketReview.objects.filter(buyer=user, listing=listing).exists():
        raise AppError(status.HTTP_409_CONFLICT, "ALREADY_REVIEWED", "You have already reviewed this transaction.")

    MarketReview.objects.create(
        listing=listing, buyer=user, seller=listing.seller,
        rating=data["rating"], comment=data.get("comment", ""),
    )
    avg = MarketReview.objects.filter(seller=listing.seller).aggregate(r=Avg("rating"))["r"]
    return {"success": True, "message": "Review submitted.", "sellerRating": float(avg or 0)}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(listing_id: str) -> MarketListing:
    listing = MarketListing.objects.filter(pk=listing_id).first()
    if not listing:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Listing not found.")
    return listing


def _assert_owner(listing: MarketListing, user, allow_admin: bool = False) -> None:
    if listing.seller != user:
        if allow_admin and getattr(user, "role", "") == "admin":
            return
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "You do not own this listing.")