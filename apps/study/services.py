"""StudyBuddy service layer."""
from datetime import datetime, timezone
from rest_framework import status
from core.exceptions import AppError
from .models import (StudyAnswer, StudyBooking, StudyGroup, StudyGroupMember,
                     StudyGroupMessage, StudyGroupSession,
                     StudyQuestion, StudyResource, Tutor)
from .serializers import (
    AnswerSerializer, BookingSerializer,
    GroupMemberSerializer, GroupMessageSerializer, GroupSerializer,
    GroupSessionSerializer, QuestionSerializer, ResourceSerializer,
    TutorSerializer,
)


def get_dashboard(user) -> dict:
    upcoming = StudyBooking.objects.filter(
        student=user, status__in=["pending", "confirmed"],
        scheduled_at__gte=datetime.now(timezone.utc)
    ).order_by("scheduled_at")[:3]
    return {
        "success": True,
        "data": {
            "tutorCount":       Tutor.objects.filter(available=True).count(),
            "groupCount":       StudyGroup.objects.filter(active=True).count(),
            "resourceCount":    StudyResource.objects.count(),
            "questionCount":    StudyQuestion.objects.count(),
            "upcomingSessions": BookingSerializer(upcoming, many=True).data,
        },
    }


# ── Tutors ────────────────────────────────────────────────────

def list_tutors(filters: dict):
    qs = Tutor.objects.filter(available=True)
    if filters.get("subject"):
        qs = qs.filter(subjects__contains=[filters["subject"]])
    if filters.get("search"):
        qs = qs.filter(user__full_name__icontains=filters["search"])
    return qs.order_by("-rating")


def upsert_tutor(data: dict, user) -> dict:
    tutor, _ = Tutor.objects.update_or_create(
        user=user,
        defaults={k: v for k, v in data.items() if v is not None},
    )
    return {"success": True, "data": TutorSerializer(tutor).data}


def get_tutor(tutor_id: str) -> dict:
    tutor = Tutor.objects.filter(pk=tutor_id).first()
    if not tutor:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Tutor not found.")
    return {"success": True, "data": TutorSerializer(tutor).data}


def create_booking(data: dict, user) -> dict:
    tutor = Tutor.objects.filter(pk=data["tutor_id"]).first()
    if not tutor:
        raise AppError(status.HTTP_404_NOT_FOUND, "TUTOR_NOT_FOUND", "Tutor not found.")
    if tutor.user == user:
        raise AppError(status.HTTP_400_BAD_REQUEST, "OWN_PROFILE", "You cannot book yourself.")

    booking = StudyBooking.objects.create(
        tutor=tutor, student=user,
        subject=data["subject"],
        scheduled_at=data["scheduled_at"],
        duration_min=data.get("duration_min", 60),
        notes=data.get("notes", ""),
    )
    try:
        from apps.study.tasks import notify_booking_request
        notify_booking_request.delay(
            str(tutor.user_id), str(booking.id),
            getattr(user, "full_name", None) or user.email, data["subject"],
        )
    except Exception:
        pass
    return {"success": True, "data": BookingSerializer(booking).data}


def update_booking(booking_id: str, new_status: str, user) -> dict:
    booking = StudyBooking.objects.filter(pk=booking_id).first()
    if not booking:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Booking not found.")

    tutor      = booking.tutor
    is_tutor   = tutor.user == user
    is_student = booking.student == user

    if new_status == "confirmed" and not is_tutor:
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Only the tutor can confirm.")
    if new_status == "cancelled" and not (is_tutor or is_student):
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN",
                       "Only the tutor or student can cancel.")

    booking.status = new_status
    booking.save(update_fields=["status"])
    try:
        notify_id = str(booking.student_id) if is_tutor else str(tutor.user_id)
        from apps.study.tasks import notify_booking_update
        notify_booking_update.delay(notify_id, str(booking.id), booking.subject, new_status)
    except Exception:
        pass
    return {"success": True, "data": BookingSerializer(booking).data}


def list_my_bookings(user):
    return StudyBooking.objects.filter(student=user).order_by("-scheduled_at")


# ── Groups ────────────────────────────────────────────────────

def list_groups(filters: dict):
    qs = StudyGroup.objects.filter(active=True)
    if filters.get("subject"):
        qs = qs.filter(subject__icontains=filters["subject"])
    return qs


def create_group(data: dict, user) -> dict:
    active = data.pop("active", True)
    group = StudyGroup.objects.create(creator=user, active=active, **data)
    # Creator automatically becomes a member flagged as admin
    StudyGroupMember.objects.create(group=group, user=user, is_admin=True)
    # Sync real count
    StudyGroup.objects.filter(pk=group.pk).update(member_count=1)
    return {"success": True, "data": GroupSerializer(group).data}


def join_group(group_id: str, user) -> dict:
    group = StudyGroup.objects.filter(pk=group_id, active=True).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")

    real_count = group.memberships.count()
    if real_count >= group.max_members:
        raise AppError(status.HTTP_409_CONFLICT, "GROUP_FULL", "This group is full.")
    if StudyGroupMember.objects.filter(group=group, user=user).exists():
        raise AppError(status.HTTP_409_CONFLICT, "ALREADY_MEMBER",
                       "You are already in this group.")

    # is_admin defaults to False for regular members
    StudyGroupMember.objects.create(group=group, user=user, is_admin=False)
    StudyGroup.objects.filter(pk=group_id).update(member_count=real_count + 1)
    return {"success": True, "message": "Joined group."}


def leave_group(group_id: str, user) -> dict:
    member = StudyGroupMember.objects.filter(group_id=group_id, user=user).first()
    if not member:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_MEMBER",
                       "You are not in this group.")
    member.delete()
    real_count = StudyGroupMember.objects.filter(group_id=group_id).count()
    StudyGroup.objects.filter(pk=group_id).update(member_count=real_count)
    return {"success": True, "message": "Left group."}


def get_group(group_id: str) -> dict:
    group = StudyGroup.objects.filter(pk=group_id).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")
    members = group.memberships.select_related("user").all()
    data = GroupSerializer(group).data
    data["members"] = GroupMemberSerializer(members, many=True).data
    return {"success": True, "data": data}


def list_group_members(filters: dict):
    qs = StudyGroupMember.objects.select_related("user", "group").all()
    if filters.get("user"):
        qs = qs.filter(user_id=filters["user"])
    if filters.get("group") or filters.get("group_id"):
        gid = filters.get("group") or filters.get("group_id")
        qs = qs.filter(group_id=gid)
    return qs


def update_group(group_id: str, data: dict, user) -> dict:
    group = StudyGroup.objects.filter(pk=group_id).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")
    if str(group.creator_id) != str(user.id):
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN",
                       "Only the group creator can update this group.")
    for key, value in data.items():
        if value is not None:
            setattr(group, key, value)
    group.save()
    return {"success": True, "data": GroupSerializer(group).data}


def delete_group(group_id: str, user) -> dict:
    group = StudyGroup.objects.filter(pk=group_id).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")
    if str(group.creator_id) != str(user.id):
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN",
                       "Only the group creator can delete this group.")
    # Explicitly delete related rows first to avoid any cascade issues
    StudyGroupMember.objects.filter(group=group).delete()
    StudyGroupMessage.objects.filter(group=group).delete()
    StudyGroupSession.objects.filter(group=group).delete()
    group.delete()
    return {"success": True}


# ── Sessions ──────────────────────────────────────────────────

def list_sessions(group_id: str) -> dict:
    group = StudyGroup.objects.filter(pk=group_id, active=True).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")
    now = datetime.now(timezone.utc)
    sessions = group.sessions.filter(scheduled_at__gte=now).select_related("proposed_by")
    return {"success": True, "data": GroupSessionSerializer(sessions, many=True).data}


def create_session(group_id: str, data: dict, user) -> dict:
    group = StudyGroup.objects.filter(pk=group_id, active=True).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")

    if not StudyGroupMember.objects.filter(group=group, user=user).exists():
        raise AppError(status.HTTP_403_FORBIDDEN, "NOT_MEMBER",
                       "You must be a group member to propose sessions.")

    session = StudyGroupSession.objects.create(
        group=group,
        proposed_by=user,
        title=data["title"],
        description=data.get("description", ""),
        location=data.get("location", ""),
        scheduled_at=data["scheduled_at"],
        duration_min=data.get("duration_min", 60),
    )
    return {"success": True, "data": GroupSessionSerializer(session).data}


def delete_session(group_id: str, session_id: str, user) -> dict:
    session = StudyGroupSession.objects.filter(pk=session_id, group_id=group_id).first()
    if not session:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Session not found.")
    group = session.group
    if str(session.proposed_by_id) != str(user.id) and str(group.creator_id) != str(user.id):
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN",
                       "Only the proposer or group creator can delete this session.")
    session.delete()
    return {"success": True}


# ── Messages ──────────────────────────────────────────────────

def list_messages(group_id: str, since_id: str | None = None) -> dict:
    group = StudyGroup.objects.filter(pk=group_id, active=True).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")

    qs = group.messages.select_related("author").order_by("created_at")
    if since_id:
        try:
            pivot = StudyGroupMessage.objects.get(pk=since_id, group=group)
            qs = qs.filter(created_at__gt=pivot.created_at)
        except StudyGroupMessage.DoesNotExist:
            pass

    return {"success": True, "data": GroupMessageSerializer(qs, many=True).data}


def post_message(group_id: str, body: str, user) -> dict:
    group = StudyGroup.objects.filter(pk=group_id, active=True).first()
    if not group:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Group not found.")

    if not StudyGroupMember.objects.filter(group=group, user=user).exists():
        raise AppError(status.HTTP_403_FORBIDDEN, "NOT_MEMBER",
                       "You must be a group member to post messages.")

    message = StudyGroupMessage.objects.create(group=group, author=user, body=body)
    return {"success": True, "data": GroupMessageSerializer(message).data}


# ── Resources ─────────────────────────────────────────────────

def list_resources(filters: dict):
    qs = StudyResource.objects.all()
    if filters.get("subject"):
        qs = qs.filter(subject__icontains=filters["subject"])
    if filters.get("resource_type"):
        qs = qs.filter(resource_type=filters["resource_type"])
    if filters.get("topic"):
        qs = qs.filter(topic__icontains=filters["topic"])
    return qs


def get_resource(resource_id) -> dict:
    resource = StudyResource.objects.filter(pk=resource_id).first()
    if not resource:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Resource not found.")
    return {"success": True, "data": ResourceSerializer(resource).data}


def record_download(resource_id) -> dict:
    updated = StudyResource.objects.filter(pk=resource_id)
    if not updated.exists():
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Resource not found.")
    resource = updated.first()
    StudyResource.objects.filter(pk=resource_id).update(
        download_count=resource.download_count + 1
    )
    resource.refresh_from_db()
    return {"success": True, "data": ResourceSerializer(resource).data}


# ── Questions & Answers ───────────────────────────────────────

def list_questions(filters: dict):
    qs = StudyQuestion.objects.all()
    if filters.get("subject"):
        qs = qs.filter(subject__icontains=filters["subject"])
    if filters.get("search"):
        qs = qs.filter(title__icontains=filters["search"])
    return qs


def create_question(data: dict, user) -> dict:
    q = StudyQuestion.objects.create(author=user, **data)
    return {"success": True, "data": QuestionSerializer(q).data}


def get_question(question_id: str) -> dict:
    q = StudyQuestion.objects.filter(pk=question_id).first()
    if not q:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Question not found.")
    data = QuestionSerializer(q).data
    data["answers"] = AnswerSerializer(q.answers.all(), many=True).data
    return {"success": True, "data": data}


def create_answer(question_id: str, body: str, user) -> dict:
    q = StudyQuestion.objects.filter(pk=question_id).first()
    if not q:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Question not found.")
    answer = StudyAnswer.objects.create(question=q, author=user, body=body)
    StudyQuestion.objects.filter(pk=question_id).update(answer_count=q.answer_count + 1)
    try:
        from apps.study.tasks import notify_new_answer
        notify_new_answer.delay(str(q.author_id), str(q.id), q.title)
    except Exception:
        pass
    return {"success": True, "data": AnswerSerializer(answer).data}


def upvote_question(question_id: str, user) -> dict:
    q = StudyQuestion.objects.filter(pk=question_id).first()
    if not q:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Question not found.")
    StudyQuestion.objects.filter(pk=question_id).update(upvotes=q.upvotes + 1)
    return {"success": True, "upvotes": q.upvotes + 1}


def accept_answer(question_id: str, answer_id: str, user) -> dict:
    q = StudyQuestion.objects.filter(pk=question_id).first()
    if not q:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Question not found.")
    if q.author != user:
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN",
                       "Only the question author can accept answers.")
    StudyAnswer.objects.filter(question=q).update(is_accepted=False)
    updated = StudyAnswer.objects.filter(pk=answer_id, question=q).update(is_accepted=True)
    if not updated:
        raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Answer not found.")
    return {"success": True, "message": "Answer accepted."}