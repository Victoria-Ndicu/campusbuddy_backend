from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("authentication", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="MarketListing",
            fields=[
                ("id",           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title",        models.CharField(max_length=200)),
                ("description",  models.TextField(blank=True, null=True)),
                ("price",        models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("category",     models.CharField(max_length=50)),
                ("condition",    models.CharField(blank=True, choices=[("new","New"),("like_new","Like New"),("good","Good"),("fair","Fair")], max_length=20, null=True)),
                ("campus_id",    models.CharField(db_index=True, max_length=80)),
                ("listing_type", models.CharField(choices=[("sale","Sale"),("donation","Donation")], default="sale", max_length=20)),
                ("status",       models.CharField(choices=[("active","Active"),("sold","Sold"),("donated","Donated"),("removed","Removed")], db_index=True, default="active", max_length=20)),
                ("image_urls",   models.JSONField(blank=True, default=list)),
                ("view_count",   models.PositiveIntegerField(default=0)),
                ("created_at",   models.DateTimeField(auto_now_add=True)),
                ("updated_at",   models.DateTimeField(auto_now=True)),
                ("seller",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_listings", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="MarketMessage",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body",       models.TextField()),
                ("channel",    models.CharField(choices=[("in_app","In-App"),("whatsapp","WhatsApp"),("email","Email")], default="in_app", max_length=20)),
                ("read",       models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="messages", to="market.marketlisting")),
                ("receiver",   models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="received_market_messages", to=settings.AUTH_USER_MODEL)),
                ("sender",     models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="sent_market_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_messages", "ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="MarketSavedListing",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_by", to="market.marketlisting")),
                ("user",       models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="saved_listings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_saved_listings"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MarketReview",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rating",     models.SmallIntegerField()),
                ("comment",    models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("buyer",      models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="market_reviews_given", to=settings.AUTH_USER_MODEL)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="reviews", to="market.marketlisting")),
                ("seller",     models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="market_reviews_received", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "market_reviews"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="MarketDonationClaim",
            fields=[
                ("id",         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status",     models.CharField(choices=[("pending","Pending"),("confirmed","Confirmed"),("rejected","Rejected")], default="pending", max_length=20)),
                ("message",    models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("claimant",   models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="donation_claims", to=settings.AUTH_USER_MODEL)),
                ("listing",    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="donation_claims", to="market.marketlisting")),
            ],
            options={"db_table": "market_donation_claims"},
            bases=(models.Model,),
        ),
        migrations.AddConstraint(
            model_name="marketsavedlisting",
            constraint=models.UniqueConstraint(fields=["user","listing"], name="unique_user_saved_listing"),
        ),
        migrations.AddConstraint(
            model_name="marketreview",
            constraint=models.UniqueConstraint(fields=["buyer","listing"], name="unique_buyer_listing_review"),
        ),
        migrations.AddConstraint(
            model_name="marketdonationclaim",
            constraint=models.UniqueConstraint(fields=["claimant","listing"], name="unique_claimant_listing"),
        ),
    ]
