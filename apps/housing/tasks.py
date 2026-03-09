from config.celery import app as celery_app


@celery_app.task(name="housing.notify_alert")
def notify_housing_alert(user_id: str, listing_id: str, title: str, rent: float):
    from core.services.notification_service import send_push_notification
    send_push_notification(
        user_id=user_id,
        title="New listing matches your alert!",
        body=f"{title} — KES {rent:.0f}/mo",
        notification_type="housing_alert",
        data={"listing_id": listing_id},
    )