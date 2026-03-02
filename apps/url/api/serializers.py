"""
apps/url/api/serializers.py

DRF serializers — input validation and output shaping only.
ZERO business logic here (that lives in the service layer).
"""
from datetime import datetime

from rest_framework import serializers

from django.conf import settings


class ShortenUrlRequestSerializer(serializers.Serializer):
    """
    Input for POST /api/v1/shorten/

    Validates the incoming payload before the service layer sees it.
    The ``validate_*`` methods perform field-level sanity checks;
    domain-level validation (SSRF, collision) lives in the service.
    """

    original_url = serializers.URLField(
        max_length=2048,
        help_text="The long URL to shorten. Must be http or https.",
    )
    custom_alias = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=16,
        min_length=3,
        help_text="Optional: 3–16 char alphanumeric alias.",
    )
    expires_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Optional ISO-8601 expiry datetime (UTC).",
    )

    def validate_custom_alias(self, value: str) -> str | None:
        if not value:
            return None
        import re
        if not re.match(r"^[a-zA-Z0-9\-]+$", value):
            raise serializers.ValidationError(
                "Alias may only contain letters, digits, and hyphens."
            )
        return value

    def validate_expires_at(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("expires_at must be in the future.")
        return value


class ShortenUrlResponseSerializer(serializers.Serializer):
    """Output for POST /api/v1/shorten/ — shapes the response."""
    short_code = serializers.CharField()
    short_url = serializers.SerializerMethodField()
    original_url = serializers.CharField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)

    def get_short_url(self, obj) -> str:
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        return f"{base_url}/api/v1/{obj['short_code']}/redirect/"


class ClickEventSerializer(serializers.Serializer):
    """Serializes ClickEvent for analytics response."""
    event_id = serializers.CharField()
    clicked_at = serializers.DateTimeField()
    ip_address = serializers.IPAddressField(allow_null=True)
    user_agent = serializers.CharField(allow_null=True)


class AnalyticsResponseSerializer(serializers.Serializer):
    """Output for GET /api/v1/<code>/analytics/"""
    short_code = serializers.CharField()
    original_url = serializers.CharField()
    total_clicks = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)
    recent_events = ClickEventSerializer(many=True)
