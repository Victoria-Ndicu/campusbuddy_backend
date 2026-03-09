from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    ClaimSerializer, CreateListingSerializer, MessageSerializer,
    ReviewSerializer, SendMessageSerializer, UpdateClaimSerializer,
    UpdateListingSerializer, MarketListingSerializer,
)


class ListingsView(APIView):
    """GET /market/listings/   POST /market/listings/"""

    def get(self, request):
        filters = {k: request.query_params.get(k) for k in
                   ["campus_id", "category", "listing_type", "status", "search"]}
        qs = services.list_listings(filters, request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(MarketListingSerializer(page, many=True).data)

    def post(self, request):
        serializer = CreateListingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.create_listing(serializer.validated_data, request.user), status=201)


class ListingDetailView(APIView):
    """GET /market/listings/<id>/   PUT /...   DELETE /..."""

    def get(self, request, pk):
        return Response(services.get_listing(str(pk), request.user))

    def put(self, request, pk):
        serializer = UpdateListingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.update_listing(str(pk), serializer.validated_data, request.user))

    def delete(self, request, pk):
        return Response(services.delete_listing(str(pk), request.user))


class UploadImageView(APIView):
    """POST /market/uploads/"""
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": {"code": "NO_FILE", "message": "No file provided."}}, status=400)
        return Response(services.upload_image(file, request.user), status=201)


class DonationClaimView(APIView):
    """POST /market/donations/<id>/claim/"""

    def post(self, request, listing_id):
        serializer = ClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.claim_donation(
            str(listing_id), serializer.validated_data.get("message", ""), request.user
        ), status=201)


class DonationClaimDetailView(APIView):
    """PATCH /market/donations/<listing_id>/claims/<claim_id>/"""

    def patch(self, request, listing_id, claim_id):
        serializer = UpdateClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.update_claim(
            str(listing_id), str(claim_id), serializer.validated_data["status"], request.user
        ))


class MessagesView(APIView):
    """POST /market/messages/"""

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.send_message(serializer.validated_data, request.user), status=201)


class ListingMessagesView(APIView):
    """GET /market/messages/<listing_id>/"""

    def get(self, request, listing_id):
        qs = services.get_messages(str(listing_id), request.user)
        return Response({"success": True, "data": MessageSerializer(qs, many=True).data})


class SavedListingsView(APIView):
    """GET /market/saved/   POST /market/saved/"""

    def get(self, request):
        qs = services.get_saved_listings(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(MarketListingSerializer(page, many=True).data)

    def post(self, request):
        listing_id = request.data.get("listing_id")
        if not listing_id:
            return Response({"error": {"code": "REQUIRED", "message": "listing_id is required."}}, status=400)
        return Response(services.toggle_save(listing_id, request.user))


class ReviewsView(APIView):
    """POST /market/reviews/"""

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.create_review(serializer.validated_data, request.user), status=201)