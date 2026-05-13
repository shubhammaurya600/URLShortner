"""
apps/url/services/url_shortener_service.py

Business logic for URL shortening.

Responsibilities (Single Responsibility Principle):
  - Validate the URL.
  - Generate a short code (with collision detection + retry).
  - Handle custom alias requests.
  - Persist via the repository interface.
  - Return a ShortUrl domain entity.

This class knows NOTHING about:
  - Django ORM (talks to IUrlRepository interface only).
  - Redis (that's the redirect service).
  - HTTP (that's the API layer).
"""
import logging
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from apps.url.domain.entities import ShortUrl
from apps.url.domain.interfaces import IUrlRepository
from shared.constants.constants import COLLISION_SALT_PREFIX, MAX_COLLISION_RETRIES
from shared.exceptions.exceptions import (
    CustomAliasConflictError,
    InvalidUrlError,
    ShortCodeCollisionError,
)
from shared.utils.base62 import generate_short_code
from shared.utils.validators import validate_custom_alias, validate_url

logger = logging.getLogger(__name__)
"""
TODO: reuired to remove all the print statements because if there print statement the server load is going to increasse
"""

class UrlShortenerService:
    """
    Orchestrates the URL shortening flow.

    Dependencies are injected, enabling mock-based unit testing.

    Example (DI in views):
        repo = PostgresUrlRepository()
        svc = UrlShortenerService(url_repository=repo)
        short_url = svc.shorten("https://example.com")
    """

    def __init__(self, url_repository: IUrlRepository) -> None:
        self._repo = url_repository

    def shorten(
        self,
        original_url: str,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
    ) -> ShortUrl:
        """
        Shorten a URL with optional custom alias and expiry.

        Algorithm:
            1. Validate URL (scheme, SSRF guard).
            2. If custom alias requested → validate + save or raise conflict.
            3. Otherwise → generate Base62 code, retry on collision (up to MAX_COLLISION_RETRIES).

        Args:
            original_url: The long URL to shorten.
            custom_alias: Optional user-defined short code.
            expires_at: Optional UTC datetime after which the URL expires.

        Returns:
            Persisted ShortUrl entity.

        Raises:
            InvalidUrlError: URL fails validation.
            CustomAliasConflictError: Custom alias already taken.
            ShortCodeCollisionError: Auto-generation exhausted all retries.
        """
        # Step 1: Validate URL
        validated_url = validate_url(original_url)

        # Step 2: Custom alias path
        if custom_alias:
            return self._shorten_with_alias(validated_url, custom_alias, expires_at)

        # Step 3: Auto-generation path with collision retry
        return self._shorten_with_retry(validated_url, expires_at)

    def _shorten_with_alias(
        self,
        original_url: str,
        alias: str,
        expires_at: datetime | None,
    ) -> ShortUrl:
        """Handle custom alias shortening."""
        validated_alias = validate_custom_alias(alias)

        if self._repo.exists(validated_alias):
            raise CustomAliasConflictError(
                f"Alias '{validated_alias}' is already taken."
            )

        entity = self._build_entity(original_url, validated_alias, expires_at)
        return self._repo.save(entity)

    def _shorten_with_retry(
        self,
        original_url: str,
        expires_at: datetime | None,
    ) -> ShortUrl:
        """
        Generate a short code with deterministic hashing + salt-based retry.

        Retry strategy:
            Attempt 0: hash(url)
            Attempt 1: hash(url + "retry_1")
            Attempt 2: hash(url + "retry_2")
            ...up to MAX_COLLISION_RETRIES

        Collision probability per attempt with 7 Base62 chars:
            Space = 62^7 ≈ 3.5 trillion codes.
            Birthday paradox threshold: ~1.8M codes for 0.1% collision rate.
            At 50M stored URLs the probability is still <0.002% per attempt.
        """
        max_retries = getattr(settings, "MAX_COLLISION_RETRIES", MAX_COLLISION_RETRIES)

        for attempt in range(max_retries):
            salt = "" if attempt == 0 else f"{COLLISION_SALT_PREFIX}_{attempt}"
            code = generate_short_code(original_url, salt=salt)

            if self._repo.exists(code):
                logger.warning(
                    "Short code collision detected: code=%s attempt=%d",
                    code,
                    attempt,
                )
                continue

            entity = self._build_entity(original_url, code, expires_at)
            try:
                return self._repo.save(entity)
            except CustomAliasConflictError:
                # Race condition: another request saved the same code
                # between our exists() check and save() → retry
                logger.warning(
                    "Race condition on code=%s attempt=%d — retrying",
                    code,
                    attempt,
                )
                continue

        raise ShortCodeCollisionError(
            f"Failed to generate a unique short code after {max_retries} attempts."
        )

    @staticmethod
    def _build_entity(
        original_url: str,
        short_code: str,
        expires_at: datetime | None,
    ) -> ShortUrl:
        """Assemble the ShortUrl domain entity (pre-persistence)."""
        return ShortUrl(
            original_url=original_url,
            short_code=short_code,
            created_at=timezone.now(),
            expires_at=expires_at,
            is_active=True,
        )
