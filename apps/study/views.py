from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination

from . import services
from .serializers import (
    AnswerSerializer, BookingSerializer, CreateAnswerSerializer,
    CreateBookingSerializer, CreateGroupSerializer, CreateQuestionSerializer,
    CreateResourceSerializer, CreateTutorSerializer, GroupSerializer,
    QuestionSerializer, ResourceSerializer, TutorSerializer,
    UpdateBookingSerializer,
)


class DashboardView(APIView):
    def get(self, request):
        return Response(services.get_dashboard(request.user))


class TutorsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["campus_id", "subject", "search"]}
        qs = services.list_tutors(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(TutorSerializer(page, many=True).data)

    def post(self, request):
        s = CreateTutorSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.upsert_tutor(s.validated_data, request.user))


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


class GroupsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["campus_id", "subject"]}
        qs = services.list_groups(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(GroupSerializer(page, many=True).data)

    def post(self, request):
        s = CreateGroupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_group(s.validated_data, request.user), status=201)


class GroupJoinView(APIView):
    def post(self, request, pk):
        return Response(services.join_group(str(pk), request.user))


class GroupLeaveView(APIView):
    def post(self, request, pk):
        return Response(services.leave_group(str(pk), request.user))


class ResourcesView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["campus_id", "subject", "resource_type"]}
        qs = services.list_resources(filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ResourceSerializer(page, many=True).data)

    def post(self, request):
        s = CreateResourceSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.create_resource(s.validated_data, request.user), status=201)


class QuestionsView(APIView):
    def get(self, request):
        filters = {k: request.query_params.get(k) for k in ["campus_id", "subject", "search"]}
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