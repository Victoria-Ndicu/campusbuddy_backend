from django.urls import path
from . import views

app_name = "market"

urlpatterns = [
    path("listings/",                                           views.ListingsView.as_view(),             name="listings"),
    path("listings/<uuid:pk>/",                                 views.ListingDetailView.as_view(),        name="listing-detail"),
    path("donations/<uuid:listing_id>/claim/",                  views.DonationClaimView.as_view(),        name="donation-claim"),
    path("donations/<uuid:listing_id>/claims/<uuid:claim_id>/", views.DonationClaimDetailView.as_view(),  name="claim-detail"),
    path("messages/",                                           views.MessagesView.as_view(),             name="messages"),
    path("messages/<uuid:listing_id>/",                         views.ListingMessagesView.as_view(),      name="listing-messages"),
    path("saved/",                                              views.SavedListingsView.as_view(),        name="saved"),
    path("reviews/",                                            views.ReviewsView.as_view(),              name="reviews"),
]