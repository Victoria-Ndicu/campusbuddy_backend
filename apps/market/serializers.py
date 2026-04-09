import base64
import filetype

from rest_framework import serializers

from .models import MarketDonationClaim, MarketListing, MarketMessage, MarketReview, MarketSavedListing


# ── Reusable base64 image field ───────────────────────────────────────────────

class Base64ImageField(serializers.Field):
    """
    Accepts a base64-encoded image string (with or without a data-URI prefix).
    Validates it is a real image and normalises it to:
        "data:<mime>;base64,<data>"
    """
    ALLOWED_MIMES  = {"image/png", "image/jpeg", "image/gif", "image/webp"}
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB per image

    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError("Expected a base64 string.")

        # Strip data-URI prefix if present
        if data.startswith("data:"):
            try:
                header, raw = data.split(",", 1)
                mime = header.split(":")[1].split(";")[0]   # e.g. "image/png"
            except (ValueError, IndexError):
                raise serializers.ValidationError("Malformed data-URI.")
        else:
            raw  = data
            mime = None

        # Decode
        try:
            decoded = base64.b64decode(raw, validate=True)
        except Exception:
            raise serializers.ValidationError("Invalid base64 encoding.")

        if len(decoded) > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError(
                f"Image exceeds {self.MAX_SIZE_BYTES // (1024 * 1024)} MB limit.")

        # Detect image type using filetype (works on Python 3.13+)
        kind = filetype.guess(decoded)
        if kind is None or kind.mime not in self.ALLOWED_MIMES:
            detected = kind.mime if kind else "unknown"
            raise serializers.ValidationError(
                f"Unsupported image type '{detected}'. "
                f"Allowed: {self.ALLOWED_MIMES}.")

        # Normalise to a consistent data-URI
        normalised_mime = mime or kind.mime
        return f"data:{normalised_mime};base64,{raw}"

    def to_representation(self, value):
        return value   # already a data-URI string


class Base64ImageListField(serializers.ListField):
    """A list of Base64ImageField values (max 5 images)."""
    child = Base64ImageField()

    def to_internal_value(self, data):
        if len(data) > 5:
            raise serializers.ValidationError("A listing may have at most 5 images.")
        return super().to_internal_value(data)


# ── Listing serializers ───────────────────────────────────────────────────────

class MarketListingSerializer(serializers.ModelSerializer):
    sellerId    = serializers.UUIDField(source="seller_id", read_only=True)
    listingType = serializers.CharField(source="listing_type")
    imageData   = serializers.JSONField(source="image_data")
    viewCount   = serializers.IntegerField(source="view_count", read_only=True)
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = MarketListing
        fields = [
            "id", "sellerId", "title", "description", "price",
            "category", "condition", "listingType", "status",
            "imageData", "viewCount", "createdAt",
        ]


class CreateListingSerializer(serializers.Serializer):
    title        = serializers.CharField(max_length=200)
    description  = serializers.CharField(required=False, allow_blank=True)
    price        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    category     = serializers.CharField(max_length=50)
    condition    = serializers.ChoiceField(choices=["new", "like_new", "good", "fair"], required=False, allow_null=True)
    listing_type = serializers.ChoiceField(choices=["sale", "donation"], default="sale")
    image_data   = Base64ImageListField(default=list, required=False)


class UpdateListingSerializer(serializers.Serializer):
    title        = serializers.CharField(max_length=200, required=False)
    description  = serializers.CharField(required=False)
    price        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    condition    = serializers.ChoiceField(choices=["new", "like_new", "good", "fair"], required=False, allow_null=True)
    status       = serializers.ChoiceField(choices=["active", "sold", "donated", "removed"], required=False)
    image_data   = Base64ImageListField(required=False)


# ── Saved listing serializer ──────────────────────────────────────────────────

class SavedListingSerializer(serializers.ModelSerializer):
    saverId = serializers.UUIDField(source="user_id", read_only=True)
    savedAt = serializers.DateTimeField(source="created_at", read_only=True)
    listing = MarketListingSerializer(read_only=True)

    class Meta:
        model  = MarketSavedListing
        fields = ["id", "saverId", "savedAt", "listing"]


# ── Message serializers ───────────────────────────────────────────────────────

class MessageSerializer(serializers.ModelSerializer):
    senderId   = serializers.UUIDField(source="sender_id", read_only=True)
    receiverId = serializers.UUIDField(source="receiver_id", read_only=True)
    listingId  = serializers.UUIDField(source="listing_id", read_only=True)
    createdAt  = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = MarketMessage
        fields = ["id", "listingId", "senderId", "receiverId", "body", "channel", "read", "createdAt"]


class SendMessageSerializer(serializers.Serializer):
    listing_id  = serializers.UUIDField()
    receiver_id = serializers.UUIDField()
    body        = serializers.CharField()
    channel     = serializers.ChoiceField(choices=["in_app", "whatsapp", "email"], default="in_app")


# ── Review / claim serializers ────────────────────────────────────────────────

class ReviewSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    rating     = serializers.IntegerField(min_value=1, max_value=5)
    comment    = serializers.CharField(required=False, allow_blank=True)


class ClaimSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)


class UpdateClaimSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["confirmed", "rejected"])