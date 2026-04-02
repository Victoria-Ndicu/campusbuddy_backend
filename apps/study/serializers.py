from rest_framework import serializers
from .models import (StudyAnswer, StudyBooking, StudyGroup, StudyGroupMember,
                     StudyGroupMessage, StudyGroupSession, StudyQuestion,
                     StudyResource, Tutor)


class TutorSerializer(serializers.ModelSerializer):
    userId     = serializers.UUIDField(source="user_id", read_only=True)
    hourlyRate = serializers.DecimalField(source="hourly_rate", max_digits=10, decimal_places=2, allow_null=True)

    class Meta:
        model  = Tutor
        fields = ["id", "userId", "subjects", "hourlyRate", "bio", "rating", "review_count", "available"]


class BookingSerializer(serializers.ModelSerializer):
    tutorId      = serializers.UUIDField(source="tutor_id", read_only=True)
    studentId    = serializers.UUIDField(source="student_id", read_only=True)
    scheduledAt  = serializers.DateTimeField(source="scheduled_at")
    durationMin  = serializers.IntegerField(source="duration_min")
    createdAt    = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyBooking
        fields = ["id", "tutorId", "studentId", "subject", "scheduledAt", "durationMin", "status", "notes", "createdAt"]


class CreateBookingSerializer(serializers.Serializer):
    tutor_id     = serializers.UUIDField()
    subject      = serializers.CharField(max_length=100)
    scheduled_at = serializers.DateTimeField()
    duration_min = serializers.IntegerField(default=60)
    notes        = serializers.CharField(required=False, allow_blank=True)


class UpdateBookingSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["confirmed", "cancelled", "completed"])


# ── Groups ────────────────────────────────────────────────────

class GroupMemberSerializer(serializers.ModelSerializer):
    """
    Returns a flat shape that the Flutter _GroupMemberRow.fromJson can parse.
    Includes both nested 'user' object AND flat user_id/full_name fields so
    the Flutter _extractId() helper works correctly with either shape.
    """
    user_id   = serializers.UUIDField(source="user.id", read_only=True)
    full_name = serializers.SerializerMethodField()
    degree    = serializers.SerializerMethodField()
    group_id  = serializers.UUIDField(source="group.id", read_only=True)
    is_online = serializers.SerializerMethodField()

    class Meta:
        model  = StudyGroupMember
        fields = ["id", "group_id", "user_id", "full_name", "degree", "is_online", "is_creator", "joined_at"]

    def get_full_name(self, obj):
        u = obj.user
        # Support both full_name field and first/last split
        return (getattr(u, "full_name", None)
                or f"{getattr(u, 'first_name', '')} {getattr(u, 'last_name', '')}".strip()
                or getattr(u, "username", "Member"))

    def get_degree(self, obj):
        u = obj.user
        return (getattr(u, "degree", None)
                or getattr(u, "program", None)
                or "")

    def get_is_online(self, obj):
        # Extend this with real presence logic if available
        return False


class GroupSerializer(serializers.ModelSerializer):
    # Return plain UUID strings — Flutter reads creator_id OR creatorId
    creatorId   = serializers.UUIDField(source="creator_id", read_only=True)
    maxMembers  = serializers.IntegerField(source="max_members")
    # Always use the real DB count to avoid drift from manual counter
    memberCount = serializers.SerializerMethodField()
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyGroup
        fields = ["id", "creatorId", "name", "subject", "description",
                  "maxMembers", "memberCount", "active", "createdAt"]

    def get_memberCount(self, obj):
        return obj.memberships.count()


class CreateGroupSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=150)
    subject     = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    max_members = serializers.IntegerField(default=10, min_value=1)
    # Accept active from Flutter but default to True — this was the root cause
    # of the "only 3 visible" bug: old serializer silently dropped active=true,
    # relying on the model default, which was fine. BUT if any groups were
    # accidentally created with active=False via Django admin or a migration,
    # they'd be filtered out. Including it here makes the intent explicit.
    active      = serializers.BooleanField(default=True, required=False)


class UpdateGroupSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    max_members = serializers.IntegerField(required=False, min_value=1)
    active      = serializers.BooleanField(required=False)


# ── Sessions ──────────────────────────────────────────────────

class GroupSessionSerializer(serializers.ModelSerializer):
    proposedById   = serializers.UUIDField(source="proposed_by_id", read_only=True)
    proposedByName = serializers.SerializerMethodField()
    groupId        = serializers.UUIDField(source="group_id", read_only=True)
    scheduledAt    = serializers.DateTimeField(source="scheduled_at")
    durationMin    = serializers.IntegerField(source="duration_min")
    createdAt      = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyGroupSession
        fields = ["id", "groupId", "proposedById", "proposedByName",
                  "title", "description", "location",
                  "scheduledAt", "durationMin", "createdAt"]

    def get_proposedByName(self, obj):
        u = obj.proposed_by
        return (getattr(u, "full_name", None)
                or f"{getattr(u, 'first_name', '')} {getattr(u, 'last_name', '')}".strip()
                or getattr(u, "username", "Member"))


class CreateSessionSerializer(serializers.Serializer):
    title        = serializers.CharField(max_length=200)
    description  = serializers.CharField(required=False, allow_blank=True, default="")
    location     = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    scheduled_at = serializers.DateTimeField()
    duration_min = serializers.IntegerField(default=60, min_value=1)


# ── Messages ──────────────────────────────────────────────────

class GroupMessageSerializer(serializers.ModelSerializer):
    authorId   = serializers.UUIDField(source="author_id", read_only=True)
    authorName = serializers.SerializerMethodField()
    groupId    = serializers.UUIDField(source="group_id", read_only=True)
    createdAt  = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyGroupMessage
        fields = ["id", "groupId", "authorId", "authorName", "body", "createdAt"]

    def get_authorName(self, obj):
        u = obj.author
        return (getattr(u, "full_name", None)
                or f"{getattr(u, 'first_name', '')} {getattr(u, 'last_name', '')}".strip()
                or getattr(u, "username", "Member"))


class CreateMessageSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1)


# ── Resources ─────────────────────────────────────────────────

class ResourceSerializer(serializers.ModelSerializer):
    resourceType   = serializers.CharField(source="resource_type", read_only=True)
    fileUrl        = serializers.URLField(source="file_url", read_only=True)
    downloadCount  = serializers.IntegerField(source="download_count", read_only=True)
    createdAt      = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyResource
        fields = [
            "id", "title", "subject", "topic",
            "resourceType", "fileUrl", "downloadCount", "createdAt",
        ]


# ── Questions & Answers ───────────────────────────────────────

class QuestionSerializer(serializers.ModelSerializer):
    authorId    = serializers.UUIDField(source="author_id", read_only=True)
    answerCount = serializers.IntegerField(source="answer_count", read_only=True)
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyQuestion
        fields = ["id", "authorId", "title", "body", "subject", "tags", "answerCount", "upvotes", "createdAt"]


class CreateQuestionSerializer(serializers.Serializer):
    title   = serializers.CharField(max_length=300)
    body    = serializers.CharField()
    subject = serializers.CharField(required=False, allow_blank=True)
    tags    = serializers.ListField(child=serializers.CharField(), default=list)


class AnswerSerializer(serializers.ModelSerializer):
    authorId   = serializers.UUIDField(source="author_id", read_only=True)
    questionId = serializers.UUIDField(source="question_id", read_only=True)
    isAccepted = serializers.BooleanField(source="is_accepted", read_only=True)
    createdAt  = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyAnswer
        fields = ["id", "questionId", "authorId", "body", "upvotes", "isAccepted", "createdAt"]


class CreateAnswerSerializer(serializers.Serializer):
    body = serializers.CharField()