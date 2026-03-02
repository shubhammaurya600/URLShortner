"""
apps/url/domain/entities.py

Pure Python domain entities. No ORM, no Django, no framework dependency.

These are the "truth" of the business domain. All business rules operate
on these objects. ORM models map TO these; they never leak out of the data layer.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ShortUrl:
    """
    Represents a shortened URL in the domain.

    Invariants enforced by the service layer (not here):
      - short_code is unique across the system.
      - original_url is a valid, non-private URL.
      - expires_at, if set, is in the future at creation time.

    ``frozen=True`` makes instances immutable (value objects).
    """
    original_url: str
    short_code: str
    created_at: datetime
    id: int | None = field(default=None)
    expires_at: datetime | None = field(default=None)
    is_active: bool = field(default=True)

    def is_expired(self, now: datetime | None = None) -> bool:
        """Return True if the URL has an expiry and it's in the past."""
        if self.expires_at is None:
            return False
        check_time = now or datetime.utcnow()
        # Handle both naive and aware datetimes gracefully
        if self.expires_at.tzinfo is not None and check_time.tzinfo is None:
            from datetime import timezone
            check_time = check_time.replace(tzinfo=timezone.utc)
        return check_time > self.expires_at

    def is_accessible(self, now: datetime | None = None) -> bool:
        """Return True if the URL exists, is active, and has not expired."""
        return self.is_active and not self.is_expired(now)


@dataclass
class ClickEvent:
    """
    Represents a single redirect/click event.

    Published to Kafka and later persisted by the consumer worker.
    ``event_id`` is set at creation and used for idempotent processing.
    """
    short_code: str
    clicked_at: datetime
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: str | None = field(default=None)
    user_agent: str | None = field(default=None)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for Kafka message payload."""
        return {
            "event_id": self.event_id,
            "short_code": self.short_code,
            "clicked_at": self.clicked_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClickEvent":
        """Deserialize from Kafka message payload."""
        from datetime import datetime
        return cls(
            event_id=data["event_id"],
            short_code=data["short_code"],
            clicked_at=datetime.fromisoformat(data["clicked_at"]),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            metadata=data.get("metadata", {}),
        )
