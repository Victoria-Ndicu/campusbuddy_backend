"""
File storage service — wraps Django's storage backend (Cloudflare R2 / S3).
All apps import upload_file() and delete_file() from here.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("campusbuddy.storage")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 5.0


def validate_image(file, max_size_mb: float = MAX_IMAGE_SIZE_MB) -> None:
    """Validate content type and size. Raises ValueError on failure."""
    content_type = getattr(file, "content_type", "")
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Only JPEG, PNG, and WebP images are allowed.")
    if file.size > max_size_mb * 1024 * 1024:
        raise ValueError(f"Image must be under {max_size_mb:.0f} MB.")


def upload_file(file, folder: str, user_id: Optional[str] = None) -> str:
    """
    Upload a file to the configured storage backend and return the public URL.
    Falls back to local storage in development if R2 is not configured.
    """
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = user_id or str(uuid.uuid4())
    ext = _get_extension(getattr(file, "content_type", "image/jpeg"))
    filename = f"{folder}/{uid}_{ts}.{ext}"

    try:
        saved_name = default_storage.save(filename, ContentFile(file.read()))
        url = default_storage.url(saved_name)
        logger.info(f"Uploaded: {url}")
        return url
    except Exception as exc:
        logger.error(f"Upload failed [{filename}]: {exc}")
        raise RuntimeError("File upload failed. Please try again.") from exc


def delete_file(url: str) -> None:
    """Delete a file from storage given its URL. Best-effort."""
    if not url:
        return
    try:
        from django.core.files.storage import default_storage
        from django.conf import settings

        r2_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "")
        if r2_domain and r2_domain in url:
            key = url.split(r2_domain)[-1].lstrip("/")
            if default_storage.exists(key):
                default_storage.delete(key)
    except Exception as exc:
        logger.warning(f"File delete failed: {exc}")


def _get_extension(content_type: str) -> str:
    mapping = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    return mapping.get(content_type, "jpg")