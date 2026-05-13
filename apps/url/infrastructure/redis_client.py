"""
apps/url/infrastructure/redis_client.py

Fail-safe Redis cache wrapper implementing the Cache-Aside pattern.

Design decisions:
  - All methods catch Redis exceptions and return None / False.
  - The service layer never sees a Redis error — the cache is transparent.
  - If Redis is unavailable the system degrades gracefully to Postgres-only.
  - Key format: short_url:{short_code}
"""
import logging
from typing import Any

import redis
from django.conf import settings

from shared.constants.constants import DEFAULT_CACHE_TTL_SECONDS, REDIS_URL_KEY_PREFIX

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Thin, fail-safe wrapper around the Redis client.

    Singleton-friendly — create once and share. Thread-safe because the
    underlying redis.Redis client uses a connection pool.
    """

    def __init__(self, redis_url: str | None = None, ttl: int | None = None) -> None:
        
        #rediss://default:gQAAAAAAASFJAAIgcDJjOTJmY2VmYjVlM2E0MzhhYmNlYzE4ZmM1MjJlZWNlMw@chief-donkey-74057.upstash.io:6379
        url = redis_url or getattr(settings, "REDIS_URL", "rediss://default:gQAAAAAAASFJAAIgcDJjOTJmY2VmYjVlM2E0MzhhYmNlYzE4ZmM1MjJlZWNlMw@chief-donkey-74057.upstash.io:6379")
        self._ttl = ttl or getattr(settings, "CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS)
        try:
            self._client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False,
            )
        except Exception as exc:
            logger.error("Failed to initialise Redis client: %s", exc)
            self._client = None  # type: ignore[assignment]

    # ─────────────────────────────────────────────
    # Cache-Aside helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def build_key(short_code: str) -> str:
        """Canonical key format: short_url:{code}"""
        return f"{REDIS_URL_KEY_PREFIX}:{short_code}"

    def get(self, short_code: str) -> str | None:
        """
        Return the cached original_url for the given short_code, or None.

        A None return means cache MISS — the caller should query Postgres.
        """
        if not self._client:
            return None
        key = self.build_key(short_code)
        try:
            value = self._client.get(key)
            if value:
                logger.debug("Cache HIT: key=%s", key)
            else:
                logger.debug("Cache MISS: key=%s", key)
            return value
        except redis.RedisError as exc:
            logger.warning("Redis GET failed (key=%s): %s", key, exc)
            return None

    def set(
        self,
        short_code: str,
        original_url: str,
        ttl: int | None = None,
    ) -> bool:
        """
        Cache an original_url under its short_code with a TTL.

        Returns True on success, False on any Redis error.
        """
        if not self._client:
            return False
        key = self.build_key(short_code)
        effective_ttl = ttl or self._ttl
        try:
            self._client.setex(key, effective_ttl, original_url)
            logger.debug("Cache SET: key=%s ttl=%ds", key, effective_ttl)
            return True
        except redis.RedisError as exc:
            logger.warning("Redis SET failed (key=%s): %s", key, exc)
            return False

    def delete(self, short_code: str) -> bool:
        """
        Remove a cached entry (cache invalidation on URL deactivation).

        Returns True if the key was deleted, False otherwise.
        """
        if not self._client:
            return False
        key = self.build_key(short_code)
        try:
            deleted = self._client.delete(key)
            logger.info("Cache DELETE: key=%s deleted=%s", key, bool(deleted))
            return bool(deleted)
        except redis.RedisError as exc:
            logger.warning("Redis DELETE failed (key=%s): %s", key, exc)
            return False

    def ping(self) -> bool:
        """Health check — returns True if Redis is reachable."""
        if not self._client:
            return False
        try:
            return self._client.ping()
        except redis.RedisError:
            return False
