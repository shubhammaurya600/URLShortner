"""
apps/url/infrastructure/kafka_producer.py

Async Kafka event producer. Publishes click events fire-and-forget.

Design decisions:
  - Uses ``acks=1`` (leader ACK only) for low-latency, high-throughput publishing.
  - ``KafkaProducer`` is instantiated lazily at first use (avoids startup failures
    when Kafka is temporarily unavailable during deployments).
  - Producer is fail-safe: if Kafka is down, we log and continue — losing a click
    event is preferable to failing a redirect.
  - Message key = short_code bytes → consistent Kafka partitioning (all events for
    the same short code go to the same partition → ordered consumption).
"""
import json
import logging
from threading import Lock

from django.conf import settings
from kafka import KafkaProducer
from kafka.errors import KafkaError

from apps.url.domain.entities import ClickEvent

logger = logging.getLogger(__name__)

_producer_lock = Lock()
_producer_instance: KafkaProducer | None = None


def _get_producer() -> KafkaProducer | None:
    """
    Lazy singleton producer.

    Thread-safe via lock. Returns None if Kafka is unreachable so callers
    can degrade gracefully.
    """
    global _producer_instance
    if _producer_instance is not None:
        return _producer_instance
    with _producer_lock:
        if _producer_instance is not None:  # double-checked locking
            return _producer_instance
        try:
            _producer_instance = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks=1,
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=3_000,
                max_block_ms=2_000,  # Don't block the redirect >2s if Kafka is slow
            )
            logger.info("Kafka producer initialised: %s", settings.KAFKA_BOOTSTRAP_SERVERS)
        except KafkaError as exc:
            logger.error("Kafka producer initialisation failed: %s", exc)
            _producer_instance = None
    return _producer_instance


class KafkaEventProducer:
    """
    Publishes click events to the ``url_click_events`` Kafka topic.

    Each instance uses the shared singleton KafkaProducer (connection pool).
    Thread-safe.

    Dependency injection for testing:
        producer = KafkaEventProducer(topic="test_topic")  # override topic
    """

    def __init__(self, topic: str | None = None) -> None:
        self._topic = topic or getattr(
            settings, "KAFKA_TOPIC_CLICK_EVENTS", "url_click_events"
        )

    def publish_click_event(self, event: ClickEvent) -> bool:
        """
        Publish a ClickEvent asynchronously to Kafka.

        The message key is the short_code, ensuring all clicks for the
        same short URL land in the same Kafka partition (ordered delivery).

        Args:
            event: The ClickEvent domain entity.

        Returns:
            True if published successfully, False if Kafka is unavailable.
        """
        producer = _get_producer()
        if producer is None:
            logger.warning(
                "Kafka unavailable, click event dropped: event_id=%s short_code=%s",
                event.event_id,
                event.short_code,
            )
            return False

        try:
            future = producer.send(
                topic=self._topic,
                key=event.short_code,
                value=event.to_dict(),
            )
            # Non-blocking: fire-and-forget with error callback
            future.add_errback(
                lambda exc: logger.error(
                    "Kafka delivery failed for event_id=%s: %s",
                    event.event_id,
                    exc,
                )
            )
            logger.debug(
                "Click event published: event_id=%s short_code=%s",
                event.event_id,
                event.short_code,
            )
            return True
        except KafkaError as exc:
            logger.error(
                "Failed to publish click event (event_id=%s): %s",
                event.event_id,
                exc,
            )
            return False

    def close(self) -> None:
        """Flush and close the producer (called on graceful shutdown)."""
        global _producer_instance
        if _producer_instance:
            try:
                _producer_instance.flush(timeout=5)
                _producer_instance.close()
                _producer_instance = None
            except KafkaError as exc:
                logger.warning("Error closing Kafka producer: %s", exc)
