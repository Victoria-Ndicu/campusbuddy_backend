"""
Email service — minimal version.
Uses Django's console email backend in development (prints to terminal).
"""
import logging

logger = logging.getLogger("campusbuddy.email")


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send email via Django's configured backend (console in dev)."""
    try:
        from django.core.mail import send_mail
        import re
        plain = re.sub(r'<[^>]+>', '', html_body).strip()
        send_mail(subject=subject, message=plain, from_email=None, recipient_list=[to], fail_silently=True)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as exc:
        logger.error(f"Email failed to {to}: {exc}")
        return False


def send_otp_email(to: str, otp: str, template: str = "verify") -> None:
    """In dev mode this prints the OTP to the terminal."""
    if template == "verify":
        subject = "Your CampusBuddy verification code"
        body = f"Your verification code is: {otp}\nExpires in 10 minutes."
    else:
        subject = "Reset your CampusBuddy password"
        body = f"Your password reset code is: {otp}\nExpires in 10 minutes."
    send_email(to=to, subject=subject, html_body=body)
    # Also log plainly so you can see it during dev without checking email
    logger.info(f"OTP for {to}: {otp}")


def send_market_message_email(to: str, sender_name: str, listing_title: str, message_body: str) -> None:
    subject = f"New message about: {listing_title}"
    body = f"{sender_name} sent: {message_body}"
    send_email(to=to, subject=subject, html_body=body)