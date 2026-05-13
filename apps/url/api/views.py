"""
apps/url/api/views.py

DRF API views — thin controllers. Zero business logic.

Each view:
  1. Validates input via a serializer.
  2. Constructs dependencies (repository + service).
  3. Calls service method.
  4. Returns a structured response.

Dependency injection note:
  In a larger system you'd wire services through a DI container (e.g. injector,
  dependency_injector). Here we use per-request instantiation which is clean,
  readable, and performs identically (Python class instantiation is ~microseconds).
"""
import io
import logging
from typing import Any

import qrcode
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.url.api.serializers import (
    AnalyticsResponseSerializer,
    ShortenUrlRequestSerializer,
    ShortenUrlResponseSerializer,
)
from apps.url.api.throttling import RedirectRateThrottle, ShortenRateThrottle
from apps.url.infrastructure.kafka_producer import KafkaEventProducer
from apps.url.infrastructure.redis_client import RedisCache
from apps.url.repositories.click_event_repository import PostgresClickEventRepository
from apps.url.repositories.url_repository import PostgresUrlRepository
from apps.url.services.analytics_service import AnalyticsService
from apps.url.services.url_redirect_service import UrlRedirectService
from apps.url.services.url_shortener_service import UrlShortenerService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────
# Dependency factories (could be replaced by a DI container)
# ─────────────────────────────────────────────────

def _make_shortener_service() -> UrlShortenerService:
    return UrlShortenerService(url_repository=PostgresUrlRepository())


def _make_redirect_service() -> UrlRedirectService:
    return UrlRedirectService(
        url_repository=PostgresUrlRepository(),
        cache=RedisCache(),
        event_producer=KafkaEventProducer(),
        click_repository=PostgresClickEventRepository(),  # DB fallback if Kafka is down
    )


def _make_analytics_service() -> AnalyticsService:
    return AnalyticsService(
        url_repository=PostgresUrlRepository(),
        click_repository=PostgresClickEventRepository(),
    )


# ─────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────

class ShortenUrlView(APIView):
    """
    POST /api/v1/shorten/

    Shorten a long URL into a short code.

    Request body:
        {
            "original_url": "https://example.com/very/long/path",
            "custom_alias": "my-link",          # optional
            "expires_at": "2027-01-01T00:00:00Z"  # optional
        }

    Response (201):
        {
            "short_code": "aB3xY7z",
            "short_url": "http://localhost:8000/api/v1/aB3xY7z/redirect/",
            "original_url": "https://...",
            "created_at": "...",
            "expires_at": null
        }
    """
    print("ShortenUrlView")
    print(APIView)
    throttle_classes = [ShortenRateThrottle]

    def post(self, request: Request) -> Response:
        serializer = ShortenUrlRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = _make_shortener_service()
        short_url = service.shorten(
            original_url=data["original_url"],
            custom_alias=data.get("custom_alias"),
            expires_at=data.get("expires_at"),
        )

        response_data = {
            "short_code": short_url.short_code,
            "original_url": short_url.original_url,
            "created_at": short_url.created_at,
            "expires_at": short_url.expires_at,
        }
        out_serializer = ShortenUrlResponseSerializer(response_data)

        logger.info(
            "URL shortened: short_code=%s",
            short_url.short_code,
        )

        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class RedirectUrlView(APIView):
    """
    GET /api/v1/<short_code>/redirect/

    Resolve a short code and redirect to the original URL.

    Response: HTTP 302 Found with Location header.
    Errors:
        404 — short code not found
        410 — URL expired or inactive
        429 — rate limit exceeded
    """
    throttle_classes = [RedirectRateThrottle]

    def get(self, request: Request, short_code: str) -> HttpResponse:
        service = _make_redirect_service()
        original_url = service.redirect(
            short_code=short_code,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        logger.info("Redirect: short_code=%s", short_code)

        response = HttpResponse(status=302)
        response["Location"] = original_url
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str | None:
        """Extract real client IP, respecting X-Forwarded-For from load balancer."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class AnalyticsView(APIView):
    """
    GET /api/v1/<short_code>/analytics/

    Return click analytics for a shortened URL.

    Response (200):
        {
            "short_code": "aB3xY7z",
            "original_url": "https://...",
            "total_clicks": 1042,
            "created_at": "...",
            "expires_at": null,
            "recent_events": [...]
        }
    """

    def get(self, request: Request, short_code: str) -> Response:
        service = _make_analytics_service()
        summary = service.get_analytics(short_code)

        serializer = AnalyticsResponseSerializer({
            "short_code": summary.short_code,
            "original_url": summary.original_url,
            "total_clicks": summary.total_clicks,
            "created_at": summary.created_at,
            "expires_at": summary.expires_at,
            "recent_events": [
                {
                    "event_id": e.event_id,
                    "clicked_at": e.clicked_at,
                    "ip_address": e.ip_address,
                    "user_agent": e.user_agent,
                }
                for e in summary.recent_events
            ],
        })

        return Response(serializer.data, status=status.HTTP_200_OK)


class QRCodeView(APIView):
    """
    GET /api/v1/<short_code>/qrcode/

    Generate and return a QR code PNG image for the short URL.

    Response: image/png binary stream.
    """

    def get(self, request: Request, short_code: str) -> HttpResponse:
        # Verify the short URL exists first
        repo = PostgresUrlRepository()
        short_url = repo.get_by_short_code(short_code)  # raises UrlNotFoundError

        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        redirect_url = f"{base_url}/api/v1/{short_code}/redirect/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(redirect_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(
            buffer.getvalue(),
            content_type="image/png",
            headers={"Content-Disposition": f'inline; filename="{short_code}.png"'},
        )


class HealthCheckView(APIView):
    """
    GET /health/

    Returns system health status.

    Response (200):
        {"status": "ok", "components": {"postgres": "ok", "redis": "ok"}}

    Response (503) if any critical component is down:
        {"status": "degraded", "components": {...}}
    """

    def get(self, request: Request) -> Response:
        components: dict[str, str] = {}
        overall_ok = True

        # Check Postgres
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            components["postgres"] = "ok"
        except Exception as exc:
            logger.error("Health check: Postgres failed: %s", exc)
            components["postgres"] = "error"
            overall_ok = False

        # Check Redis
        try:
            cache = RedisCache()
            components["redis"] = "ok" if cache.ping() else "error"
            if components["redis"] == "error":
                overall_ok = False
        except Exception as exc:
            logger.error("Health check: Redis failed: %s", exc)
            components["redis"] = "error"

        http_status = status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(
            {
                "status": "ok" if overall_ok else "degraded",
                "components": components,
            },
            status=http_status,
        )
