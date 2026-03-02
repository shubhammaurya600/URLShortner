"""
apps/url/api/urls.py

URL routing for the URL shortener API.

Versioned under /api/v1/ for future API evolution.
"""
from django.urls import path

from apps.url.api.views import (
    AnalyticsView,
    HealthCheckView,
    QRCodeView,
    RedirectUrlView,
    ShortenUrlView,
)

app_name = "url"

urlpatterns = [
    # ─────────────────────────────────────────────
    # Core endpoints
    # ─────────────────────────────────────────────

    # POST — Shorten a long URL
    path(
        "api/v1/shorten/",
        ShortenUrlView.as_view(),
        name="shorten",
    ),

    # GET — Redirect to original URL (the hot path)
    path(
        "api/v1/<str:short_code>/redirect/",
        RedirectUrlView.as_view(),
        name="redirect",
    ),

    # ─────────────────────────────────────────────
    # Analytics & utilities
    # ─────────────────────────────────────────────

    # GET — Click analytics for a short code
    path(
        "api/v1/<str:short_code>/analytics/",
        AnalyticsView.as_view(),
        name="analytics",
    ),

    # GET — QR code PNG image for a short URL
    path(
        "api/v1/<str:short_code>/qrcode/",
        QRCodeView.as_view(),
        name="qrcode",
    ),

    # ─────────────────────────────────────────────
    # Operations
    # ─────────────────────────────────────────────

    # GET — System health check
    path(
        "health/",
        HealthCheckView.as_view(),
        name="health",
    ),
]
