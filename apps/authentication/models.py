"""
Authentication models.
Custom User model extends AbstractBaseUser for full control over fields.
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # uses Django's bcrypt hasher
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email, password, **extra_fields)


class AllowedEmailDomain(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    institution_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.institution_name} ({self.domain})"

    class Meta:
        ordering = ['institution_name']

        
class User(AbstractBaseUser, PermissionsMixin):
    """
    Central user model. Auth module owns this table.
    Profile columns are defined here too (one table, added via migrations).
    """

    ROLE_CHOICES = [("student", "Student"), ("admin", "Admin")]

    # ── Auth fields ────────────────────────────────────────────────────────────
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True, db_index=True)
    phone       = models.CharField(max_length=30, blank=True, null=True)
    role        = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    is_verified = models.BooleanField(default=False)
    is_staff    = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # ── Profile fields (co-located — no separate profile table needed) ─────────
    full_name     = models.CharField(max_length=120, blank=True, null=True)
    degree        = models.CharField(max_length=120, blank=True, null=True)
    year_of_study = models.SmallIntegerField(blank=True, null=True)
    university    = models.CharField(max_length=160, blank=True, null=True)
    avatar_url    = models.URLField(max_length=500, blank=True, null=True)

    # ── Soft delete ────────────────────────────────────────────────────────────
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class OtpCode(models.Model):
    """Single-use OTP for email verification and password reset."""

    OTP_TYPE_CHOICES = [
        ("email_verify", "Email Verification"),
        ("password_reset", "Password Reset"),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code       = models.CharField(max_length=255)          # stored as bcrypt hash
    otp_type   = models.CharField(max_length=30, choices=OTP_TYPE_CHOICES)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)
    attempts   = models.SmallIntegerField(default=0)       # max 5 before invalidation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_codes"
        ordering = ["-created_at"]

    @classmethod
    def generate(cls, user: "User", otp_type: str, expiry_minutes: int = 10) -> tuple["OtpCode", str]:
        """
        Create a new OTP record.
        Returns (OtpCode instance, plain_text_code).
        The plain text code is sent via email; only the hash is stored.
        """
        from django.contrib.auth.hashers import make_password

        plain = f"{secrets.randbelow(10000):04d}"
        record = cls.objects.create(
            user=user,
            code=make_password(plain),
            otp_type=otp_type,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
        )
        return record, plain

    def verify(self, plain: str) -> bool:
        """Check the submitted code against the stored hash."""
        from django.contrib.auth.hashers import check_password
        return check_password(plain, self.code)

    def __str__(self):
        return f"OTP[{self.otp_type}] for {self.user.email}"

    