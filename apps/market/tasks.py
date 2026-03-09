"""
Celery tasks for CampusMarket.
All push notifications are sent asynchronously to avoid blocking the request.
"""
from config.celery import app as celery_app


@celery_app.task(name="market.notify_new_message")
def notify_new_message(receiver_id: str, listing_id: str, listing_title: str, preview: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(
        user_id=receiver_id,
        title=f"New message about: {listing_title}",
        body=preview,
        notification_type="market_message",
        data={"listing_id": listing_id},
    )


@celery_app.task(name="market.notify_donation_claim")
def notify_donation_claim(seller_id: str, listing_id: str, listing_title: str):
    from core.services.notification_service import send_push_notification
    send_push_notification(
        user_id=seller_id,
        title="New donation claim",
        body=f"Someone wants your '{listing_title}'",
        notification_type="donation_claim",
        data={"listing_id": listing_id},
    )