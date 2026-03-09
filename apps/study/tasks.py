from config.celery import app as celery_app


@celery_app.task(name="study.notify_booking_request")
def notify_booking_request(tutor_user_id: str, booking_id: str, student_name: str, subject: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(user_id=tutor_user_id, title="New booking request",
                           body=f"{student_name} wants a {subject} session",
                           notification_type="study_booking_request", data={"booking_id": booking_id})


@celery_app.task(name="study.notify_booking_update")
def notify_booking_update(user_id: str, booking_id: str, subject: str, new_status: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(user_id=user_id, title="Booking update",
                           body=f"Your {subject} session has been {new_status}.",
                           notification_type="study_booking_update", data={"booking_id": booking_id})


@celery_app.task(name="study.notify_new_answer")
def notify_new_answer(author_id: str, question_id: str, question_title: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(user_id=author_id, title="New answer on your question",
                           body=question_title, notification_type="study_new_answer",
                           data={"question_id": question_id})


@celery_app.task(name="study.cleanup_otps")
def cleanup_expired_otps():
    """Daily cleanup of used/expired OTPs."""
    from datetime import datetime, timezone
    from apps.authentication.models import OtpCode
    deleted, _ = OtpCode.objects.filter(expires_at__lt=datetime.now(timezone.utc)).delete()
    import logging
    logging.getLogger("campusbuddy").info(f"Cleaned up {deleted} expired OTP records.")


@celery_app.task(name="study.hard_delete_accounts")
def hard_delete_old_accounts():
    """Monthly hard-delete of accounts soft-deleted > 30 days ago."""
    from datetime import datetime, timedelta, timezone
    from apps.authentication.models import User
    cutoff   = datetime.now(timezone.utc) - timedelta(days=30)
    deleted, _ = User.objects.filter(deleted_at__isnull=False, deleted_at__lt=cutoff).delete()
    import logging
    logging.getLogger("campusbuddy").info(f"Hard-deleted {deleted} accounts.")