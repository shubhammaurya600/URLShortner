"""
apps/url/models.py

Django ORM models. These are ONLY the persistence layer — they must NOT
contain any business logic per the "Avoid Fat Models" principle.

Mapping to domain entities is done in the repository layer.
"""
from django.db import models


class UrlModel(models.Model):
    """
    Persistence model for shortened URLs.

    Maps to the domain entity ``ShortUrl``.
    Business rules live in ``UrlShortenerService``, not here.
    """

    original_url = models.TextField(
        help_text="The original long URL that was shortened."
    )
    short_code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        help_text="The unique short identifier (Base62, 7-16 chars).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,  # Partial index defined in Meta for performance
        help_text="Optional expiry. NULL means never expires.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Soft-delete flag. Inactive URLs return 410 Gone.",
    )

    class Meta:
        db_table = "urls"
        ordering = ["-created_at"]
        indexes = [
            # Partial index on expires_at only for rows that have it set
            models.Index(
                fields=["expires_at"],
                name="idx_urls_expires_at",
                condition=models.Q(expires_at__isnull=False),
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["short_code"],
                name="uq_urls_short_code",
            ),
        ]

    def __str__(self) -> str:
        return f"<UrlModel short_code={self.short_code}>"


class ClickEventModel(models.Model):
    """
    Persistence model for individual redirect/click events.

    Written by the Kafka consumer worker (async). NOT written during
    the hot redirect path — that would block the response.
    """

    event_id = models.UUIDField(
        unique=True,
        help_text="Idempotency key — duplicate Kafka messages are safely ignored.",
    )
    short_code = models.CharField(
        max_length=16,
        db_index=True,
        help_text="Denormalized short code (avoids FK join on hot read path).",
    )
    clicked_at = models.DateTimeField(db_index=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Anonymized or raw client IP.",
    )
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Arbitrary event metadata (country, device, etc.).",
    )

    class Meta:
        db_table = "click_events"
        ordering = ["-clicked_at"]
        indexes = [
            models.Index(
                fields=["short_code", "-clicked_at"],
                name="idx_click_code_time",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event_id"],
                name="uq_click_event_id",
            ),
        ]

    def __str__(self) -> str:
        return f"<ClickEventModel short_code={self.short_code} at={self.clicked_at}>"
