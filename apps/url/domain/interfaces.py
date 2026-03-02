"""
apps/url/domain/interfaces.py

Abstract repository interfaces (Dependency Inversion Principle — D in SOLID).

The service layer depends on these abstractions, not on concrete ORM
implementations. This makes the service layer fully testable with mock
repositories and swappable data stores.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from apps.url.domain.entities import ClickEvent, ShortUrl


class IUrlRepository(ABC):
    """
    Contract for URL persistence operations.

    All methods raise domain-level exceptions (not Django ORM exceptions)
    so callers never need to import anything from django.db.
    """

    @abstractmethod
    def save(self, short_url: ShortUrl) -> ShortUrl:
        """
        Persist a new ShortUrl entity.

        Args:
            short_url: The ShortUrl entity to save.

        Returns:
            The saved entity (may include DB-generated id, created_at).

        Raises:
            CustomAliasConflictError: If short_code already exists.
        """
        ...

    @abstractmethod
    def get_by_short_code(self, short_code: str) -> ShortUrl:
        """
        Retrieve a ShortUrl by its short code.

        Args:
            short_code: The unique short identifier.

        Returns:
            The matching ShortUrl entity.

        Raises:
            UrlNotFoundError: If no record matches.
        """
        ...

    @abstractmethod
    def exists(self, short_code: str) -> bool:
        """
        Check whether a short code exists without raising an exception.

        Args:
            short_code: The short identifier to check.

        Returns:
            True if the code exists, False otherwise.
        """
        ...

    @abstractmethod
    def deactivate(self, short_code: str) -> None:
        """
        Mark a short URL as inactive (soft delete).

        Args:
            short_code: The short identifier to deactivate.

        Raises:
            UrlNotFoundError: If the code does not exist.
        """
        ...

    @abstractmethod
    def delete_expired(self, before: datetime) -> int:
        """
        Hard-delete all URLs whose expires_at is before the given datetime.

        Args:
            before: Cutoff datetime.

        Returns:
            Number of records deleted.
        """
        ...


class IClickEventRepository(ABC):
    """Contract for click event persistence (analytics store)."""

    @abstractmethod
    def save(self, event: ClickEvent) -> ClickEvent:
        """
        Persist a single click event idempotently.

        Uses event_id for deduplication — safe to call multiple times
        with the same event (idempotent).

        Args:
            event: The ClickEvent entity.

        Returns:
            The saved (or pre-existing) entity.
        """
        ...

    @abstractmethod
    def count_by_short_code(self, short_code: str) -> int:
        """
        Return the total click count for a short code.

        Args:
            short_code: The URL's short identifier.

        Returns:
            Total number of click events recorded.
        """
        ...

    @abstractmethod
    def get_recent_events(
        self, short_code: str, limit: int = 100
    ) -> list[ClickEvent]:
        """
        Retrieve the most recent click events for a short code.

        Args:
            short_code: The URL short identifier.
            limit: Maximum number of events to return.

        Returns:
            List of ClickEvent entities, newest first.
        """
        ...
