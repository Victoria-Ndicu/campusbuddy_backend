"""
Authentication service layer.
Views call these functions; no business logic lives in views.py.
"""
import logging
from datetime import datetime, timezone

from django.conf import settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.exceptions import AppError
from core.services.email_service import send_otp_email

from .models import AllowedEmailDomain, OtpCode, User

logger = logging.getLogger("campusbuddy.auth")


def register_user(email: str, password: str, phone: str = "") -> dict:
    """Create a new unverified user and dispatch a verification OTP."""
    if User.objects.filter(email=email).exists():
        raise AppError(status.HTTP_409_CONFLICT, "EMAIL_TAKEN", "An account with this email already exists.")

    # ── Auto-set university from email domain ──────────────────────────────────
    domain = email.split("@")[-1].lower()
    university = None
    try:
        allowed = AllowedEmailDomain.objects.get(domain=domain, is_active=True)
        university = allowed.institution_name
    except AllowedEmailDomain.DoesNotExist:
        pass  # Non-university email — university stays None

    user = User.objects.create_user(
        email=email,
        password=password,
        phone=phone or None,
        university=university,   # ← set once at registration, never changed after
    )

    otp_record, plain = OtpCode.generate(user, "email_verify", settings.OTP_EXPIRY_MINUTES)
    send_otp_email(to=email, otp=plain, template="verify")

    logger.info(f"Registered new user: {email} | university: {university}")
    return {"message": "Account created. Check your email for the verification code."}


def verify_otp(email: str, code: str) -> dict:
    """Verify the email OTP and return JWT tokens on success."""
    user = _get_active_user(email, must_be_verified=False)
    otp_record = _get_valid_otp(user, "email_verify")

    _check_attempts(otp_record)

    if not otp_record.verify(code):
        otp_record.attempts += 1
        otp_record.save(update_fields=["attempts"])
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_OTP", "Incorrect verification code.")

    otp_record.used = True
    otp_record.save(update_fields=["used"])

    user.is_verified = True
    user.save(update_fields=["is_verified"])

    return _build_token_response(user)


def login_user(email: str, password: str) -> dict:
    """Authenticate and return JWT tokens."""
    try:
        user = User.objects.get(email=email, deleted_at__isnull=True)
    except User.DoesNotExist:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Incorrect email or password.")

    if not user.check_password(password):
        raise AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Incorrect email or password.")

    if not user.is_verified:
        raise AppError(status.HTTP_403_FORBIDDEN, "EMAIL_NOT_VERIFIED", "Please verify your email first.")

    logger.info(f"User logged in: {email}")
    return _build_token_response(user)


def refresh_tokens(refresh_token: str) -> dict:
    """Rotate a refresh token and return a new token pair."""
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        user = User.objects.get(pk=token["user_id"], deleted_at__isnull=True)
        return _build_token_response(user)
    except Exception:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "TOKEN_INVALID", "Refresh token is invalid or expired.")


def forgot_password(email: str) -> dict:
    """Send a password reset OTP. Always returns 200 to prevent email enumeration."""
    try:
        user = User.objects.get(email=email, is_verified=True, deleted_at__isnull=True)
        otp_record, plain = OtpCode.generate(user, "password_reset", settings.OTP_EXPIRY_MINUTES)
        send_otp_email(to=email, otp=plain, template="reset")
    except User.DoesNotExist:
        pass  # Intentionally silent
    return {"message": "If an account with that email exists, reset instructions have been sent."}


def reset_password(email: str, code: str, new_password: str) -> dict:
    """Validate reset OTP and update the user's password."""
    user = _get_active_user(email, must_be_verified=True)
    otp_record = _get_valid_otp(user, "password_reset")

    _check_attempts(otp_record)

    if not otp_record.verify(code):
        otp_record.attempts += 1
        otp_record.save(update_fields=["attempts"])
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_OTP", "Incorrect reset code.")

    otp_record.used = True
    otp_record.save(update_fields=["used"])

    user.set_password(new_password)
    user.save(update_fields=["password"])

    _blacklist_all_tokens(user)

    return {"message": "Password updated successfully."}


def logout_user(refresh_token: str) -> dict:
    """Blacklist the refresh token, ending the session."""
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        pass  # Best-effort — always return success
    return {"message": "Logged out."}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _get_active_user(email: str, must_be_verified: bool = True) -> User:
    q = User.objects.filter(email=email, deleted_at__isnull=True)
    if must_be_verified:
        q = q.filter(is_verified=True)
    user = q.first()
    if not user:
        raise AppError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "No account found with this email.")
    return user


def _get_valid_otp(user: User, otp_type: str) -> OtpCode:
    otp = (
        OtpCode.objects
        .filter(
            user=user,
            otp_type=otp_type,
            used=False,
            expires_at__gt=datetime.now(timezone.utc),
        )
        .order_by("-created_at")
        .first()
    )
    if not otp:
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_OTP", "Code not found or expired. Please request a new one.")
    return otp


def _check_attempts(otp: OtpCode) -> None:
    if otp.attempts >= settings.MAX_OTP_ATTEMPTS:
        otp.used = True
        otp.save(update_fields=["used"])
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "OTP_MAX_ATTEMPTS",
            "Too many failed attempts. Please request a new code.",
        )


def _build_token_response(user: User) -> dict:
    """Generate a fresh token pair and return the standard response shape."""
    from .serializers import UserBriefSerializer

    refresh = RefreshToken.for_user(user)
    refresh["email"] = user.email
    refresh["role"] = user.role

    return {
        "accessToken": str(refresh.access_token),
        "refreshToken": str(refresh),
        "user": UserBriefSerializer(user).data,
    }


def _blacklist_all_tokens(user: User) -> None:
    """Blacklist all outstanding refresh tokens for a user (best-effort)."""
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            try:
                RefreshToken(token.token).blacklist()
            except Exception:
                pass
    except Exception:
        pass