import logging

logger = logging.getLogger("campusbuddy.email")


def send_email(to: str, subject: str, html_body: str) -> bool:
    try:
        from django.core.mail import send_mail
        import re
        plain = re.sub(r'<[^>]+>', '', html_body).strip()
        send_mail(subject=subject, message=plain, from_email=None,
                  recipient_list=[to], fail_silently=True)
        return True
    except Exception as exc:
        logger.error(f"Email failed to {to}: {exc}")
        return False


def send_otp_email(to: str, otp: str, template: str = "verify") -> None:
    if template == "verify":
        subject = "Your CampusBuddy verification code"
    else:
        subject = "Reset your CampusBuddy password"

    print("\n" + "="*50)
    print(f"  OTP CODE for {to}")
    print(f"  Code: {otp}")
    print(f"  Type: {template}")
    print("="*50 + "\n", flush=True)

    send_email(to=to, subject=subject, html_body=f"Your code is: {otp}")


def send_market_message_email(to: str, sender_name: str, listing_title: str, message_body: str) -> None:
    send_email(
        to=to,
        subject=f"New message about: {listing_title}",
        html_body=f"{sender_name} sent: {message_body}",
    )
