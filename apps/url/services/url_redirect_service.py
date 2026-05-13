"""
apps/url/services/url_redirect_service.py

Business logic for the redirect hot path.

This is the most performance-critical service. Every redirect goes through here.
Strategy:
  1. Check Redis (sub-millisecond if hit).
  2. On miss → query Postgres → populate Redis → return.
  3. Try to publish a ClickEvent to Kafka (async).
  4. If Kafka is unavailable, fall back to writing the click directly to the DB.

The Redis check and Kafka publish are both fail-safe: their errors
DO NOT prevent the redirect from succeeding.
"""
import logging
from datetime import datetime

from django.utils import timezone

from apps.url.domain.entities import ClickEvent
from apps.url.domain.interfaces import IClickEventRepository, IUrlRepository
from apps.url.infrastructure.kafka_producer import KafkaEventProducer
from apps.url.infrastructure.redis_client import RedisCache
from shared.exceptions.exceptions import UrlExpiredError, UrlInactiveError, UrlNotFoundError

logger = logging.getLogger(__name__)


class UrlRedirectService:
    """
    Handles the redirect flow with Cache-Aside pattern + Kafka event publishing.

    Injected dependencies:
        - url_repository:   IUrlRepository        (DB access)
        - cache:            RedisCache             (cache-aside)
        - event_producer:   KafkaEventProducer    (async analytics via Kafka)
        - click_repository: IClickEventRepository (direct DB fallback when Kafka is down)
    """

    def __init__(
        self,
        url_repository: IUrlRepository,
        cache: RedisCache,
        event_producer: KafkaEventProducer,
        click_repository: IClickEventRepository | None = None,
    ) -> None:
        self._repo = url_repository
        self._cache = cache
        self._event_producer = event_producer
        self._click_repo = click_repository

    def redirect(
        self,
        short_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """
        Resolve a short code to its original URL and fire a click event.

        Cache-Aside read path:
            1. Try Redis.
            2. On miss → Postgres → hydrate cache.
            3. Validate expiry & active status.
            4. Publish Kafka event (fire-and-forget).

        Args:
            short_code: The short URL identifier.
            ip_address: Client IP (for analytics).
            user_agent: Client User-Agent header (for analytics).

        Returns:
            The original (long) URL to redirect to.

        Raises:
            UrlNotFoundError: Code does not exist.
            UrlExpiredError: Code exists but is past expiry.
            UrlInactiveError: Code has been deactivated.
        """
        original_url = self._resolve_url(short_code)
        self._publish_click_event(short_code, original_url, ip_address, user_agent)
        return original_url

    def _resolve_url(self, short_code: str) -> str:
        """
        Cache-Aside resolution.

        Note: We cache the URL string directly (not the full entity) to keep
        the Redis payload minimal and avoid deserialization on the hot path.
        For expiry validation, we fall through to Postgres on cache miss so
        we can check ``is_active`` and ``expires_at``.
        """
        # 1. Cache hit
        cached = self._cache.get(short_code)
        if cached:
            return cached

        # 2. Cache miss → Postgres (this is the cold path)
        short_url = self._repo.get_by_short_code(short_code)  # raises UrlNotFoundError

        # 3. Validate
        now = timezone.now()
        if not short_url.is_active:
            raise UrlInactiveError()
        if short_url.is_expired(now):
            raise UrlExpiredError()

        # 4. Populate cache (lazy loading) — fail-safe
        self._cache.set(short_code, short_url.original_url)

        return short_url.original_url

    def _publish_click_event(
        self,
        short_code: str,
        original_url: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        """
        Record a click event.

        Primary path: publish to Kafka asynchronously (fire-and-forget).
        Fallback path: if Kafka is unavailable and a click_repository was
        injected, write the event directly to the database so analytics
        are never silently dropped.

        The redirect MUST NOT be blocked by analytics in either path.
        """
        event = ClickEvent(
            short_code=short_code,
            clicked_at=timezone.now(),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        published = self._event_producer.publish_click_event(event)

        # Fallback: Kafka unavailable → write directly to DB
        if not published and self._click_repo is not None:
            try:
                self._click_repo.save(event)
                logger.info(
                    "Click event saved directly to DB (Kafka fallback): "
                    "short_code=%s event_id=%s",
                    short_code,
                    event.event_id,
                )
            except Exception as exc:
                logger.error(
                    "Failed to save click event to DB fallback: "
                    "short_code=%s event_id=%s error=%s",
                    short_code,
                    event.event_id,
                    exc,
                )

    def invalidate_cache(self, short_code: str) -> None:
        """
        Remove a URL from the cache (called on deactivation/deletion).

        Args:
            short_code: The code to evict from cache.
        """
        self._cache.delete(short_code)
        logger.info("Cache invalidated: short_code=%s", short_code)
