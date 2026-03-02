"""
apps/url/repositories/url_repository.py

Concrete implementation of IUrlRepository using Django ORM.

This is the ONLY file that knows about Django ORM models.
The service layer is completely unaware of ORM specifics.
"""
import logging
from datetime import datetime

from django.db import IntegrityError
from django.utils import timezone

from apps.url.domain.entities import ShortUrl
from apps.url.domain.interfaces import IUrlRepository
from apps.url.models import UrlModel
from shared.exceptions.exceptions import CustomAliasConflictError, UrlNotFoundError

logger = logging.getLogger(__name__)


class PostgresUrlRepository(IUrlRepository):
    """
    IUrlRepository implementation backed by PostgreSQL via Django ORM.

    Stateless — no shared mutable state. Safe to instantiate per-request
    or share as a singleton.
    """

    def save(self, short_url: ShortUrl) -> ShortUrl:
        """
        Persist a ShortUrl entity. Raises CustomAliasConflictError on
        UNIQUE constraint violation so callers never see an IntegrityError.
        """
        try:
            model = UrlModel.objects.create(
                original_url=short_url.original_url,
                short_code=short_url.short_code,
                created_at=short_url.created_at,
                expires_at=short_url.expires_at,
                is_active=short_url.is_active,
            )
            logger.info(
                "Saved short URL: short_code=%s", short_url.short_code
            )
            return self._to_entity(model)
        except IntegrityError:
            raise CustomAliasConflictError(
                f"Short code '{short_url.short_code}' is already in use."
            )

    def get_by_short_code(self, short_code: str) -> ShortUrl:
        """
        Fetch a ShortUrl by code. Raises UrlNotFoundError if absent.
        """
        try:
            model = UrlModel.objects.get(short_code=short_code)
            return self._to_entity(model)
        except UrlModel.DoesNotExist:
            raise UrlNotFoundError(
                f"Short code '{short_code}' does not exist."
            )

    def exists(self, short_code: str) -> bool:
        return UrlModel.objects.filter(short_code=short_code).exists()

    def deactivate(self, short_code: str) -> None:
        updated = UrlModel.objects.filter(short_code=short_code).update(
            is_active=False
        )
        if updated == 0:
            raise UrlNotFoundError(
                f"Cannot deactivate: short code '{short_code}' not found."
            )

    def delete_expired(self, before: datetime) -> int:
        count, _ = UrlModel.objects.filter(
            expires_at__lt=before, expires_at__isnull=False
        ).delete()
        logger.info("Deleted %d expired URLs (before=%s)", count, before)
        return count

    # ─────────────────────────────────────────────
    # Mapping helpers — ORM model → domain entity
    # ─────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: UrlModel) -> ShortUrl:
        """Map an ORM model instance to a domain entity (no ORM leakage)."""
        return ShortUrl(
            id=model.pk,
            original_url=model.original_url,
            short_code=model.short_code,
            created_at=model.created_at,
            expires_at=model.expires_at,
            is_active=model.is_active,
        )
