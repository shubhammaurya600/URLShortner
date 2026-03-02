"""
apps/url/tests/test_services.py

Unit tests for service layer using mock repositories.

No database, Redis, or Kafka needed — pure unit tests.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase

from apps.url.domain.entities import ClickEvent, ShortUrl
from apps.url.domain.interfaces import IClickEventRepository, IUrlRepository
from apps.url.services.analytics_service import AnalyticsService
from apps.url.services.url_redirect_service import UrlRedirectService
from apps.url.services.url_shortener_service import UrlShortenerService
from shared.exceptions.exceptions import (
    CustomAliasConflictError,
    ShortCodeCollisionError,
    UrlExpiredError,
    UrlInactiveError,
    UrlNotFoundError,
)


def _make_short_url(**kwargs) -> ShortUrl:
    """Helper to build a ShortUrl test fixture."""
    defaults = {
        "id": 1,
        "original_url": "https://example.com/test",
        "short_code": "abc1234",
        "created_at": datetime.now(tz=timezone.utc),
        "expires_at": None,
        "is_active": True,
    }
    defaults.update(kwargs)
    return ShortUrl(**defaults)


class TestUrlShortenerService(TestCase):
    """Unit tests for UrlShortenerService."""

    def setUp(self):
        self.mock_repo = MagicMock(spec=IUrlRepository)

    def _make_service(self) -> UrlShortenerService:
        return UrlShortenerService(url_repository=self.mock_repo)

    def test_shorten_returns_short_url_entity(self):
        saved = _make_short_url()
        self.mock_repo.exists.return_value = False
        self.mock_repo.save.return_value = saved

        svc = self._make_service()
        result = svc.shorten("https://www.example.com/some/long/path")

        self.mock_repo.save.assert_called_once()
        self.assertIsInstance(result, ShortUrl)
        self.assertEqual(result.short_code, "abc1234")

    def test_shorten_with_custom_alias(self):
        saved = _make_short_url(short_code="my-link")
        self.mock_repo.exists.return_value = False
        self.mock_repo.save.return_value = saved

        svc = self._make_service()
        result = svc.shorten("https://example.com", custom_alias="my-link")

        self.assertEqual(result.short_code, "my-link")

    def test_custom_alias_conflict_raises(self):
        self.mock_repo.exists.return_value = True  # alias already taken

        svc = self._make_service()
        with self.assertRaises(CustomAliasConflictError):
            svc.shorten("https://example.com", custom_alias="taken")

    def test_collision_retry_succeeds_on_third_attempt(self):
        """Mock exists() to return True for first 2 codes, then False."""
        saved = _make_short_url()
        call_count = {"n": 0}

        def exists_side_effect(code):
            call_count["n"] += 1
            return call_count["n"] < 3  # First 2 calls say "exists", 3rd says "free"

        self.mock_repo.exists.side_effect = exists_side_effect
        self.mock_repo.save.return_value = saved

        svc = self._make_service()
        result = svc.shorten("https://example.com")
        self.assertIsInstance(result, ShortUrl)
        self.assertGreaterEqual(call_count["n"], 3)

    def test_collision_exhaustion_raises(self):
        """All MAX_COLLISION_RETRIES attempts fail → ShortCodeCollisionError."""
        self.mock_repo.exists.return_value = True  # always collides

        svc = self._make_service()
        with self.assertRaises(ShortCodeCollisionError):
            svc.shorten("https://example.com/always-collides")

    def test_invalid_url_raises(self):
        """Private IP SSRF attempt should be blocked by validator."""
        svc = self._make_service()
        with self.assertRaises(Exception):
            # 127.0.0.1 is a private/loopback address
            svc.shorten("http://127.0.0.1/admin")


class TestUrlRedirectService(TestCase):
    """Unit tests for UrlRedirectService."""

    def setUp(self):
        self.mock_repo = MagicMock(spec=IUrlRepository)
        self.mock_cache = MagicMock()
        self.mock_producer = MagicMock()

    def _make_service(self) -> UrlRedirectService:
        return UrlRedirectService(
            url_repository=self.mock_repo,
            cache=self.mock_cache,
            event_producer=self.mock_producer,
        )

    def test_redirect_cache_hit_skips_db(self):
        """On cache hit, the repository should NOT be called."""
        self.mock_cache.get.return_value = "https://example.com/original"

        svc = self._make_service()
        result = svc.redirect("abc1234")

        self.assertEqual(result, "https://example.com/original")
        self.mock_repo.get_by_short_code.assert_not_called()

    def test_redirect_cache_miss_queries_db_and_caches(self):
        """On cache miss, DB is queried and result is cached."""
        self.mock_cache.get.return_value = None  # cache miss
        short_url = _make_short_url(original_url="https://example.com/real")
        self.mock_repo.get_by_short_code.return_value = short_url

        svc = self._make_service()
        result = svc.redirect("abc1234")

        self.assertEqual(result, "https://example.com/real")
        self.mock_repo.get_by_short_code.assert_called_once_with("abc1234")
        self.mock_cache.set.assert_called_once()

    def test_redirect_publishes_kafka_event(self):
        """A click event should be published after every successful redirect."""
        self.mock_cache.get.return_value = "https://example.com"

        svc = self._make_service()
        svc.redirect("abc1234", ip_address="1.2.3.4", user_agent="Test/1.0")

        self.mock_producer.publish_click_event.assert_called_once()

    def test_redirect_expired_url_raises(self):
        self.mock_cache.get.return_value = None
        expired_url = _make_short_url(
            expires_at=datetime.now(tz=timezone.utc) - timedelta(days=1)
        )
        self.mock_repo.get_by_short_code.return_value = expired_url

        svc = self._make_service()
        with self.assertRaises(UrlExpiredError):
            svc.redirect("abc1234")

    def test_redirect_inactive_url_raises(self):
        self.mock_cache.get.return_value = None
        inactive_url = _make_short_url(is_active=False)
        self.mock_repo.get_by_short_code.return_value = inactive_url

        svc = self._make_service()
        with self.assertRaises(UrlInactiveError):
            svc.redirect("abc1234")

    def test_redirect_not_found_raises(self):
        self.mock_cache.get.return_value = None
        self.mock_repo.get_by_short_code.side_effect = UrlNotFoundError()

        svc = self._make_service()
        with self.assertRaises(UrlNotFoundError):
            svc.redirect("nonexistent")

    def test_redis_failure_falls_through_to_db(self):
        """If Redis raises, the service should still work via Postgres."""
        self.mock_cache.get.return_value = None  # Redis miss (or error → None)
        short_url = _make_short_url(original_url="https://fallback.example.com")
        self.mock_repo.get_by_short_code.return_value = short_url

        svc = self._make_service()
        result = svc.redirect("abc1234")
        self.assertEqual(result, "https://fallback.example.com")


class TestAnalyticsService(TestCase):
    """Unit tests for AnalyticsService."""

    def setUp(self):
        self.mock_url_repo = MagicMock(spec=IUrlRepository)
        self.mock_click_repo = MagicMock(spec=IClickEventRepository)

    def _make_service(self) -> AnalyticsService:
        return AnalyticsService(
            url_repository=self.mock_url_repo,
            click_repository=self.mock_click_repo,
        )

    def test_get_analytics_returns_summary(self):
        self.mock_url_repo.get_by_short_code.return_value = _make_short_url()
        self.mock_click_repo.count_by_short_code.return_value = 42
        self.mock_click_repo.get_recent_events.return_value = []

        svc = self._make_service()
        summary = svc.get_analytics("abc1234")

        self.assertEqual(summary.total_clicks, 42)
        self.assertEqual(summary.short_code, "abc1234")
        self.assertEqual(summary.original_url, "https://example.com/test")

    def test_get_analytics_not_found_raises(self):
        self.mock_url_repo.get_by_short_code.side_effect = UrlNotFoundError()

        svc = self._make_service()
        with self.assertRaises(UrlNotFoundError):
            svc.get_analytics("missing")
