"""
apps/url/repositories/click_event_repository.py

Concrete implementation of IClickEventRepository using Django ORM.

Key design: uses get_or_create with event_id for idempotency.
"""
import logging
import uuid
from datetime import datetime

from apps.url.domain.entities import ClickEvent
from apps.url.domain.interfaces import IClickEventRepository
from apps.url.models import ClickEventModel

logger = logging.getLogger(__name__)


class PostgresClickEventRepository(IClickEventRepository):
    """
    IClickEventRepository backed by PostgreSQL.

    Idempotent by design: ``save()`` uses ``get_or_create`` on ``event_id``
    so re-delivered Kafka messages are safe to process multiple times.
    """

    def save(self, event: ClickEvent) -> ClickEvent:
        """
        Persist a ClickEvent. Idempotent — duplicate event_ids are ignored.
        """
        model, created = ClickEventModel.objects.get_or_create(
            event_id=event.event_id,
            defaults={
                "short_code": event.short_code,
                "clicked_at": event.clicked_at,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "metadata": event.metadata,
            },
        )
        if not created:
            logger.debug(
                "Duplicate click event ignored: event_id=%s", event.event_id
            )
        else:
            logger.info(
                "Click event saved: event_id=%s short_code=%s",
                event.event_id,
                event.short_code,
            )
        return self._to_entity(model)

    def count_by_short_code(self, short_code: str) -> int:
        return ClickEventModel.objects.filter(short_code=short_code).count()

    def get_recent_events(
        self, short_code: str, limit: int = 100
    ) -> list[ClickEvent]:
        models = (
            ClickEventModel.objects.filter(short_code=short_code)
            .order_by("-clicked_at")[:limit]
        )
        return [self._to_entity(m) for m in models]

    # ─────────────────────────────────────────────
    # Mapping helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: ClickEventModel) -> ClickEvent:
        return ClickEvent(
            event_id=str(model.event_id),
            short_code=model.short_code,
            clicked_at=model.clicked_at,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            metadata=model.metadata or {},
        )
