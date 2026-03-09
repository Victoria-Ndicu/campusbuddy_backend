from rest_framework import serializers
from .models import MarketDonationClaim, MarketListing, MarketMessage, MarketReview, MarketSavedListing


class MarketListingSerializer(serializers.ModelSerializer):
    sellerId    = serializers.UUIDField(source="seller_id", read_only=True)
    listingType = serializers.CharField(source="listing_type")
    imageUrls   = serializers.JSONField(source="image_urls")
    viewCount   = serializers.IntegerField(source="view_count", read_only=True)
    campusId    = serializers.CharField(source="campus_id")
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = MarketListing
        fields = [
            "id", "sellerId", "title", "description", "price", "category",
            "condition", "campusId", "listingType", "status",
            "imageUrls", "viewCount", "createdAt",
        ]


class CreateListingSerializer(serializers.Serializer):
    title       = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    price       = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    category    = serializers.CharField(max_length=50)
    condition   = serializers.ChoiceField(choices=["new", "like_new", "good", "fair"], required=False, allow_null=True)
    campus_id   = serializers.CharField(max_length=80)
    listing_type = serializers.ChoiceField(choices=["sale", "donation"], default="sale")
    image_urls  = serializers.ListField(child=serializers.URLField(), default=list)


class UpdateListingSerializer(serializers.Serializer):
    title        = serializers.CharField(max_length=200, required=False)
    description  = serializers.CharField(required=False)
    price        = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    condition    = serializers.ChoiceField(choices=["new", "like_new", "good", "fair"], required=False, allow_null=True)
    status       = serializers.ChoiceField(choices=["active", "sold", "donated", "removed"], required=False)
    image_urls   = serializers.ListField(child=serializers.URLField(), required=False)


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


class ReviewSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    rating     = serializers.IntegerField(min_value=1, max_value=5)
    comment    = serializers.CharField(required=False, allow_blank=True)


class ClaimSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)


class UpdateClaimSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["confirmed", "rejected"])