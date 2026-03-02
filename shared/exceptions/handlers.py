"""
shared/exceptions/handlers.py

Custom DRF exception handler — converts domain exceptions and Django
exceptions into consistent JSON error envelopes.

Response format:
    {
        "error": {
            "code": "url_not_found",
            "message": "Short URL not found.",
            "detail": null
        }
    }
"""
import logging
from typing import Any

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import exception_handler

from shared.exceptions.exceptions import AppBaseException

logger = logging.getLogger(__name__)


def _snake(cls_name: str) -> str:
    """Convert CamelCase class name to snake_case error code."""
    import re
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", cls_name).lower()
    # strip trailing _error
    return s.removesuffix("_error")


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Wraps DRF's default handler and additionally handles:
    - AppBaseException subclasses (domain errors)
    - Django's Http404
    """
    # 1. Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is not None:
        # Re-format DRF error response
        response.data = {
            "error": {
                "code": _extract_drf_code(exc),
                "message": _flatten_errors(response.data),
                "detail": None,
            }
        }
        return response

    # 2. Handle domain exceptions
    if isinstance(exc, AppBaseException):
        logger.warning(
            "Domain exception: %s",
            exc.message,
            extra={"exc_type": type(exc).__name__},
        )
        return Response(
            {
                "error": {
                    "code": _snake(type(exc).__name__),
                    "message": exc.message,
                    "detail": None,
                }
            },
            status=exc.status_code,
        )

    # 3. Unhandled — log and return 500
    logger.exception("Unhandled exception: %s", exc)
    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "detail": None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_drf_code(exc: Exception) -> str:
    if isinstance(exc, APIException):
        return getattr(exc, "default_code", "api_error")
    if isinstance(exc, Http404):
        return "not_found"
    return "api_error"


def _flatten_errors(data: Any) -> str:
    """Flatten nested DRF error structures into a single string."""
    if isinstance(data, list):
        return " ".join(str(item) for item in data)
    if isinstance(data, dict):
        parts = []
        for key, val in data.items():
            if isinstance(val, list):
                parts.append(f"{key}: {' '.join(str(v) for v in val)}")
            else:
                parts.append(f"{key}: {val}")
        return " | ".join(parts)
    return str(data)
