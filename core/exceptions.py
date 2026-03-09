"""
Global exception handler for Django REST Framework.
Returns a consistent JSON envelope: { "success": false, "error": { "code": "...", "message": "..." } }
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("campusbuddy")


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler.
    Wraps all errors in a consistent envelope so the Flutter client
    can always read error.code and error.message.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled it — reformat the payload
        detail = response.data

        # Flatten DRF's nested error dicts into a single message
        if isinstance(detail, dict):
            if "detail" in detail:
                message = str(detail["detail"])
                code = getattr(detail["detail"], "code", "ERROR") or "ERROR"
            else:
                # Field-level validation errors — pick the first one
                first_field = next(iter(detail))
                first_error = detail[first_field]
                if isinstance(first_error, list):
                    message = f"{first_field}: {first_error[0]}"
                    code = getattr(first_error[0], "code", "VALIDATION_ERROR") or "VALIDATION_ERROR"
                else:
                    message = str(first_error)
                    code = "VALIDATION_ERROR"
        elif isinstance(detail, list):
            message = str(detail[0])
            code = getattr(detail[0], "code", "ERROR") or "ERROR"
        else:
            message = str(detail)
            code = "ERROR"

        response.data = {
            "success": False,
            "error": {
                "code": str(code).upper(),
                "message": message,
            },
        }
        return response

    # Unhandled exception — return 500
    logger.exception("Unhandled server error", exc_info=exc)
    return Response(
        {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class AppError(Exception):
    """
    Raise this inside a service to return a structured API error.

    Usage:
        raise AppError(status.HTTP_409_CONFLICT, "EMAIL_TAKEN", "Email is already registered.")
    """

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)