from rest_framework import serializers
from .models import StudyAnswer, StudyBooking, StudyGroup, StudyQuestion, StudyResource, Tutor


class TutorSerializer(serializers.ModelSerializer):
    userId     = serializers.UUIDField(source="user_id", read_only=True)
    hourlyRate = serializers.DecimalField(source="hourly_rate", max_digits=10, decimal_places=2, allow_null=True)
    campusId   = serializers.CharField(source="campus_id")

    class Meta:
        model  = Tutor
        fields = ["id", "userId", "subjects", "hourlyRate", "bio", "rating", "review_count", "available", "campusId"]


class CreateTutorSerializer(serializers.Serializer):
    subjects    = serializers.ListField(child=serializers.CharField())
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    bio         = serializers.CharField(required=False)
    campus_id   = serializers.CharField(max_length=80)


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


class GroupSerializer(serializers.ModelSerializer):
    creatorId   = serializers.UUIDField(source="creator_id", read_only=True)
    maxMembers  = serializers.IntegerField(source="max_members")
    memberCount = serializers.IntegerField(source="member_count", read_only=True)
    campusId    = serializers.CharField(source="campus_id")
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyGroup
        fields = ["id", "creatorId", "name", "subject", "description", "maxMembers", "memberCount", "campusId", "active", "createdAt"]


class CreateGroupSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=150)
    subject     = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False)
    max_members = serializers.IntegerField(default=10)
    campus_id   = serializers.CharField(max_length=80)


class UpdateGroupSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    max_members = serializers.IntegerField(required=False)
    active      = serializers.BooleanField(required=False)


class ResourceSerializer(serializers.ModelSerializer):
    uploaderId    = serializers.UUIDField(source="uploader_id", read_only=True)
    resourceType  = serializers.CharField(source="resource_type")
    fileUrl       = serializers.URLField(source="file_url")
    downloadCount = serializers.IntegerField(source="download_count", read_only=True)
    campusId      = serializers.CharField(source="campus_id")
    createdAt     = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyResource
        fields = ["id", "uploaderId", "title", "subject", "resourceType", "fileUrl", "downloadCount", "campusId", "createdAt"]


class CreateResourceSerializer(serializers.Serializer):
    title         = serializers.CharField(max_length=200)
    subject       = serializers.CharField(max_length=100)
    resource_type = serializers.ChoiceField(choices=["pdf", "doc", "video", "link", "other"])
    file_url      = serializers.URLField()
    campus_id     = serializers.CharField(max_length=80)


class QuestionSerializer(serializers.ModelSerializer):
    authorId    = serializers.UUIDField(source="author_id", read_only=True)
    answerCount = serializers.IntegerField(source="answer_count", read_only=True)
    campusId    = serializers.CharField(source="campus_id")
    createdAt   = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model  = StudyQuestion
        fields = ["id", "authorId", "title", "body", "subject", "tags", "answerCount", "upvotes", "campusId", "createdAt"]


class CreateQuestionSerializer(serializers.Serializer):
    title     = serializers.CharField(max_length=300)
    body      = serializers.CharField()
    subject   = serializers.CharField(required=False)
    tags      = serializers.ListField(child=serializers.CharField(), default=list)
    campus_id = serializers.CharField(max_length=80)


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