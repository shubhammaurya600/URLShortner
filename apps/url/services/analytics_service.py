"""
apps/url/services/analytics_service.py

Provides analytics data for shortened URLs.

Reads from the click_events table (written by the Kafka consumer).
This is query-only — no mutation.
"""
import logging
from dataclasses import dataclass
from datetime import datetime

from apps.url.domain.entities import ClickEvent
from apps.url.domain.interfaces import IClickEventRepository, IUrlRepository
from shared.exceptions.exceptions import UrlNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalyticsSummary:
    """
    Read-model for analytics data — not a domain entity.
    Returned by AnalyticsService and serialized by the API layer.
    """
    short_code: str
    original_url: str
    total_clicks: int
    created_at: datetime
    expires_at: datetime | None
    recent_events: list[ClickEvent]


class AnalyticsService:
    """
    Aggregates click analytics for a given short URL.

    Dependencies injected:
        - url_repository:   IUrlRepository        (fetch URL metadata)
        - click_repository: IClickEventRepository (click counts + events)
    """

    def __init__(
        self,
        url_repository: IUrlRepository,
        click_repository: IClickEventRepository,
    ) -> None:
        self._url_repo = url_repository
        self._click_repo = click_repository

    def get_analytics(
        self,
        short_code: str,
        recent_limit: int = 20,
    ) -> AnalyticsSummary:
        """
        Return analytics summary for a short URL.

        Args:
            short_code: The short URL identifier.
            recent_limit: Max number of recent events to include.

        Returns:
            AnalyticsSummary with click count and recent events.

        Raises:
            UrlNotFoundError: If the short code does not exist.
        """
        # Will raise UrlNotFoundError if not found
        short_url = self._url_repo.get_by_short_code(short_code)

        total_clicks = self._click_repo.count_by_short_code(short_code)
        recent_events = self._click_repo.get_recent_events(
            short_code, limit=recent_limit
        )
        print("recent_events", recent_events)
        print("total_clicks", total_clicks)
        print("short_url", short_url)
        print("short_code", short_code)

        logger.info(
            "Analytics fetched: short_code=%s total_clicks=%d",
            short_code,
            total_clicks,
        )

        return AnalyticsSummary(
            short_code=short_code,
            original_url=short_url.original_url,
            total_clicks=total_clicks,
            created_at=short_url.created_at,
            expires_at=short_url.expires_at,
            recent_events=recent_events,
        )
