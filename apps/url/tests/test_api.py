"""
apps/url/tests/test_api.py

Integration tests for the REST API layer.

These tests use Django's test client + an in-memory SQLite DB.
They exercise the full stack: view → service → repository → DB.
Redis and Kafka are mocked to avoid external dependencies.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.url.models import ClickEventModel, UrlModel


class BaseApiTestCase(TestCase):
    """Base class with common setup for all API tests."""

    def setUp(self):
        self.client = APIClient()

    def _create_url(self, short_code: str = "abc1234", original_url: str = "https://example.com") -> UrlModel:
        return UrlModel.objects.create(
            short_code=short_code,
            original_url=original_url,
            is_active=True,
        )


class TestShortenEndpoint(BaseApiTestCase):
    """Tests for POST /api/v1/shorten/"""

    ENDPOINT = "/api/v1/shorten/"

    @patch("apps.url.api.views.RedisCache")
    @patch("apps.url.api.views.KafkaEventProducer")
    def test_shorten_success(self, mock_kafka, mock_redis):
        mock_redis.return_value.get.return_value = None
        response = self.client.post(
            self.ENDPOINT,
            {"original_url": "https://www.example.com/very/long/path"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("short_code", data)
        self.assertIn("short_url", data)
        self.assertIn("original_url", data)
        self.assertEqual(len(data["short_code"]), 7)

    def test_shorten_missing_url_returns_400(self):
        response = self.client.post(self.ENDPOINT, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shorten_invalid_url_returns_400(self):
        response = self.client.post(
            self.ENDPOINT,
            {"original_url": "not-a-valid-url"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.url.api.views.RedisCache")
    @patch("apps.url.api.views.KafkaEventProducer")
    def test_shorten_with_custom_alias(self, mock_kafka, mock_redis):
        response = self.client.post(
            self.ENDPOINT,
            {"original_url": "https://example.com", "custom_alias": "my-link"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["short_code"], "my-link")

    @patch("apps.url.api.views.RedisCache")
    @patch("apps.url.api.views.KafkaEventProducer")
    def test_shorten_duplicate_alias_returns_409(self, mock_kafka, mock_redis):
        # First create the alias
        self._create_url(short_code="my-alias")
        response = self.client.post(
            self.ENDPOINT,
            {"original_url": "https://example.com/new", "custom_alias": "my-alias"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_shorten_future_expires_at(self):
        future = (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()
        response = self.client.post(
            self.ENDPOINT,
            {"original_url": "https://example.com", "expires_at": future},
            format="json",
        )
        # Should not 400 on a valid future expiry
        self.assertNotEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shorten_past_expires_at_returns_400(self):
        past = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
        response = self.client.post(
            self.ENDPOINT,
            {"original_url": "https://example.com", "expires_at": past},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestRedirectEndpoint(BaseApiTestCase):
    """Tests for GET /api/v1/<short_code>/redirect/"""

    @patch("apps.url.api.views.KafkaEventProducer")
    @patch("apps.url.api.views.RedisCache")
    def test_redirect_cache_miss_goes_to_db(self, mock_redis_cls, mock_kafka_cls):
        self._create_url(short_code="abc1234", original_url="https://target.example.com")
        mock_redis_cls.return_value.get.return_value = None  # cache miss
        mock_redis_cls.return_value.set.return_value = True

        response = self.client.get("/api/v1/abc1234/redirect/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://target.example.com")

    @patch("apps.url.api.views.KafkaEventProducer")
    @patch("apps.url.api.views.RedisCache")
    def test_redirect_cache_hit(self, mock_redis_cls, mock_kafka_cls):
        mock_redis_cls.return_value.get.return_value = "https://cached.example.com"

        response = self.client.get("/api/v1/anyhit1/redirect/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://cached.example.com")

    def test_redirect_not_found_returns_404(self):
        with patch("apps.url.api.views.RedisCache") as mock_redis:
            mock_redis.return_value.get.return_value = None
            response = self.client.get("/api/v1/notexist/redirect/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.url.api.views.KafkaEventProducer")
    @patch("apps.url.api.views.RedisCache")
    def test_redirect_expired_url_returns_410(self, mock_redis_cls, mock_kafka_cls):
        expired = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        UrlModel.objects.create(
            short_code="expired1",
            original_url="https://example.com",
            expires_at=expired,
            is_active=True,
        )
        mock_redis_cls.return_value.get.return_value = None

        response = self.client.get("/api/v1/expired1/redirect/")
        self.assertEqual(response.status_code, 410)

    @patch("apps.url.api.views.KafkaEventProducer")
    @patch("apps.url.api.views.RedisCache")
    def test_redirect_inactive_url_returns_410(self, mock_redis_cls, mock_kafka_cls):
        UrlModel.objects.create(
            short_code="inactive1",
            original_url="https://example.com",
            is_active=False,
        )
        mock_redis_cls.return_value.get.return_value = None

        response = self.client.get("/api/v1/inactive1/redirect/")
        self.assertEqual(response.status_code, 410)


class TestAnalyticsEndpoint(BaseApiTestCase):
    """Tests for GET /api/v1/<short_code>/analytics/"""

    def test_analytics_returns_200_with_click_count(self):
        self._create_url(short_code="ana1234")
        response = self.client.get("/api/v1/ana1234/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("total_clicks", data)
        self.assertEqual(data["total_clicks"], 0)
        self.assertEqual(data["short_code"], "ana1234")

    def test_analytics_not_found_returns_404(self):
        response = self.client.get("/api/v1/missing9/analytics/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestHealthCheckEndpoint(BaseApiTestCase):
    """Tests for GET /health/"""

    def test_health_check_returns_200_when_healthy(self):
        with patch("apps.url.api.views.RedisCache") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            response = self.client.get("/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("postgres", data["components"])
        self.assertIn("redis", data["components"])
