import uuid
from django.conf import settings
from django.db import models


class MarketListing(models.Model):
    TYPE_CHOICES      = [("sale", "Sale"), ("donation", "Donation")]
    STATUS_CHOICES    = [("active", "Active"), ("sold", "Sold"), ("donated", "Donated"), ("removed", "Removed")]
    CONDITION_CHOICES = [("new", "New"), ("like_new", "Like New"), ("good", "Good"), ("fair", "Fair")]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True, null=True)
    price        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category     = models.CharField(max_length=50)
    condition    = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    listing_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="sale")
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    # Images stored as a JSON list of base64-encoded strings, e.g. ["data:image/png;base64,..."]
    image_data   = models.JSONField(default=list, blank=True)
    view_count   = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "market_listings"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def owner(self):
        return self.seller


class MarketMessage(models.Model):
    CHANNEL_CHOICES = [("in_app", "In-App"), ("whatsapp", "WhatsApp"), ("email", "Email")]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing    = models.ForeignKey(MarketListing, on_delete=models.CASCADE, related_name="messages")
    sender     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_market_messages")
    receiver   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_market_messages")
    body       = models.TextField()
    channel    = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="in_app")
    read       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "market_messages"
        ordering = ["created_at"]


class MarketSavedListing(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 'user' is the person who saved/bookmarked the listing
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_listings")
    listing    = models.ForeignKey(MarketListing, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "market_saved_listings"
        unique_together = [["user", "listing"]]


class MarketReview(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing    = models.ForeignKey(MarketListing, on_delete=models.CASCADE, related_name="reviews")
    buyer      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="market_reviews_given")
    seller     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="market_reviews_received")
    rating     = models.SmallIntegerField()   # 1–5
    comment    = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "market_reviews"
        unique_together = [["buyer", "listing"]]


class MarketDonationClaim(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("confirmed", "Confirmed"), ("rejected", "Rejected")]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing    = models.ForeignKey(MarketListing, on_delete=models.CASCADE, related_name="donation_claims")
    claimant   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="donation_claims")
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    message    = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "market_donation_claims"
        unique_together = [["claimant", "listing"]]