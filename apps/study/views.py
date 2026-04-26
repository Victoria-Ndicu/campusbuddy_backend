from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    AnswerSerializer, BookingSerializer,
    CreateAnswerSerializer, CreateBookingSerializer,
    CreateGroupSerializer, CreateMessageSerializer,
    CreateQuestionSerializer, CreateSessionSerializer,
    CreateTutorReviewSerializer,
    GroupMemberSerializer, GroupMessageSerializer,
    GroupSerializer, GroupSessionSerializer,
    QuestionSerializer, ResourceSerializer,
    TutorReviewSerializer, TutorSerializer,
    UpdateBookingSerializer, UpdateGroupSerializer,
)


class DashboardView(APIView):
    def get(self, request):
        return Response(services.get_dashboard(request.user))


class TutorsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["subject", "search"]}
        qs = services.list_tutors(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(TutorSerializer(page, many=True).data)


class TutorDetailView(APIView):
    def get(self, request, pk):
        return Response(services.get_tutor(str(pk)))


class TutorReviewsView(APIView):
    """
    GET  /api/v1/study-buddy/tutors/<pk>/reviews/
         Returns a paginated list of anonymous reviews for a tutor, newest first.
    POST /api/v1/study-buddy/tutors/<pk>/reviews/
         Submit a new anonymous review. Authenticated users only.
         No reviewer identity is stored or returned.
    """

    def get(self, request, pk):
        qs = services.get_tutor_reviews_queryset(str(pk))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(TutorReviewSerializer(page, many=True).data)

    def post(self, request, pk):
        s = CreateTutorReviewSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = services.create_tutor_review(str(pk), s.validated_data["message"], request.user)
        return Response(result, status=201)


class BookingsView(APIView):
    def get(self, request):
        qs = services.list_my_bookings(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(BookingSerializer(page, many=True).data)

    def post(self, request):
        s = CreateBookingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_booking(s.validated_data, request.user), status=201)


class BookingDetailView(APIView):
    def patch(self, request, pk):
        s = UpdateBookingSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.update_booking(str(pk), s.validated_data["status"], request.user))


# ── Groups ────────────────────────────────────────────────────

class GroupsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["subject"]}
        qs = services.list_groups(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(GroupSerializer(page, many=True).data)

    def post(self, request):
        s = CreateGroupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_group(s.validated_data, request.user), status=201)


class GroupDetailView(APIView):
    def get(self, request, pk):
        return Response(services.get_group(str(pk)))

    def patch(self, request, pk):
        s = UpdateGroupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.update_group(str(pk), s.validated_data, request.user))

    def delete(self, request, pk):
        return Response(services.delete_group(str(pk), request.user))


class GroupJoinView(APIView):
    def post(self, request, pk):
        return Response(services.join_group(str(pk), request.user))


class GroupLeaveView(APIView):
    def post(self, request, pk):
        return Response(services.leave_group(str(pk), request.user))


class GroupMembersView(APIView):
    """
    GET /api/v1/study-buddy/group-members/
    Query params:
      ?user=<uuid>      → memberships for a specific user (used by Flutter to
                          populate _joinedGroupIds on the browse screen)
      ?group=<uuid>     → members of a specific group
      ?group_id=<uuid>  → alias for ?group=
    Returns a paginated list of GroupMemberSerializer rows.
    This is the missing endpoint that caused joined-state to always reset.
    """
    def get(self, request):
        filters = {k: request.query_params.get(k)
                   for k in ["user", "group", "group_id"]}
        qs = services.list_group_members(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(GroupMemberSerializer(page, many=True).data)


# ── Sessions ──────────────────────────────────────────────────

class GroupSessionsView(APIView):
    """
    GET  /api/v1/study-buddy/groups/<pk>/sessions/  → list upcoming sessions
    POST /api/v1/study-buddy/groups/<pk>/sessions/  → propose a new session
    """
    def get(self, request, pk):
        return Response(services.list_sessions(str(pk)))

    def post(self, request, pk):
        s = CreateSessionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_session(str(pk), s.validated_data, request.user), status=201)


class GroupSessionDetailView(APIView):
    """
    DELETE /api/v1/study-buddy/groups/<pk>/sessions/<session_pk>/
    Proposer or group creator can delete a session.
    """
    def delete(self, request, pk, session_pk):
        return Response(services.delete_session(str(pk), str(session_pk), request.user))


# ── Messages ──────────────────────────────────────────────────

class GroupMessagesView(APIView):
    """
    GET  /api/v1/study-buddy/groups/<pk>/messages/
         Optional ?since_id=<uuid> for polling — returns only messages newer
         than the given message id. Flutter polls every 5 s while screen is open.
    POST /api/v1/study-buddy/groups/<pk>/messages/
         Body: { "body": "..." }
         Only group members can post.
    """
    def get(self, request, pk):
        since_id = request.query_params.get("since_id")
        return Response(services.list_messages(str(pk), since_id=since_id))

    def post(self, request, pk):
        s = CreateMessageSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.post_message(str(pk), s.validated_data["body"], request.user), status=201)


# ── Resources ─────────────────────────────────────────────────

class ResourcesView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["subject", "resource_type", "topic"]}
        qs = services.list_resources(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ResourceSerializer(page, many=True).data)


class ResourceDetailView(APIView):
    def get(self, request, pk):
        return Response(services.get_resource(pk))


class ResourceDownloadView(APIView):
    def post(self, request, pk):
        return Response(services.record_download(pk))


# ── Questions & Answers ───────────────────────────────────────

class QuestionsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["subject", "search"]}
        qs = services.list_questions(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(QuestionSerializer(page, many=True).data)

    def post(self, request):
        s = CreateQuestionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_question(s.validated_data, request.user), status=201)


class QuestionDetailView(APIView):
    def get(self, request, pk):
        return Response(services.get_question(str(pk)))


class AnswersView(APIView):
    def post(self, request, question_pk):
        s = CreateAnswerSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_answer(str(question_pk), s.validated_data["body"], request.user), status=201)


class UpvoteQuestionView(APIView):
    def post(self, request, pk):
        return Response(services.upvote_question(str(pk), request.user))


class AcceptAnswerView(APIView):
    def patch(self, request, question_pk, answer_pk):
        return Response(services.accept_answer(str(question_pk), str(answer_pk), request.user))