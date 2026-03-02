"""
apps/url/infrastructure/kafka_consumer.py

Kafka consumer worker. Deployed as a standalone process (not a Django view).

Started via:
    python manage.py run_kafka_consumer

Design decisions:
  - Subscribes to ``url_click_events`` topic in consumer group.
  - Commits offsets AFTER successful processing (at-least-once delivery).
  - Idempotency is handled in ``PostgresClickEventRepository.save()```
    via ``get_or_create(event_id=...)``.
  - Runs in a single thread; scale horizontally by adding more K8s pods
    (each in the same consumer group → Kafka partitions distributed).
"""
import json
import logging
import signal
import sys
import os

import django
from django.conf import settings
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class ClickEventConsumer:
    """
    Consumes click events from Kafka and persists them via the repository.

    Separation of concerns:
      - This class handles Kafka protocol (polling, committing).
      - ``PostgresClickEventRepository`` handles persistence.
      - ``ClickEvent.from_dict()`` handles deserialization.
    """

    def __init__(
        self,
        bootstrap_servers: str | None = None,
        topic: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._topic = topic or settings.KAFKA_TOPIC_CLICK_EVENTS
        self._group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        self._running = True
        self._consumer: KafkaConsumer | None = None

        # Lazy import to avoid circular imports at module level
        from apps.url.repositories.click_event_repository import PostgresClickEventRepository
        self._repository = PostgresClickEventRepository()

    def start(self) -> None:
        """
        Connect to Kafka and begin polling loop.

        Registers SIGTERM / SIGINT handlers for graceful shutdown.
        """
        self._register_signal_handlers()

        logger.info(
            "Starting Kafka consumer: topic=%s group=%s servers=%s",
            self._topic,
            self._group_id,
            self._bootstrap_servers,
        )

        try:
            self._consumer = KafkaConsumer(
                self._topic,
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=False,  # Manual commit after processing
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                session_timeout_ms=30_000,
                heartbeat_interval_ms=10_000,
                max_poll_records=500,
            )
        except KafkaError as exc:
            logger.error("Failed to create Kafka consumer: %s", exc)
            return

        logger.info("Kafka consumer connected. Waiting for messages...")
        self._poll_loop()

    def _poll_loop(self) -> None:
        """Main polling loop. Processes messages in batches."""
        assert self._consumer is not None
        try:
            while self._running:
                records = self._consumer.poll(timeout_ms=1_000)
                for partition_records in records.values():
                    for record in partition_records:
                        self._process_record(record)
                # Commit after processing the entire batch
                if records:
                    self._consumer.commit()
        except Exception as exc:
            logger.exception("Fatal error in consumer poll loop: %s", exc)
        finally:
            self._shutdown()

    def _process_record(self, record) -> None:
        """
        Process a single Kafka record.

        On any error, log and skip (dead-letter queue in future iteration).
        """
        try:
            from apps.url.domain.entities import ClickEvent
            event = ClickEvent.from_dict(record.value)
            self._repository.save(event)
            logger.debug(
                "Processed click event: event_id=%s short_code=%s",
                event.event_id,
                event.short_code,
            )
        except Exception as exc:
            logger.error(
                "Failed to process record offset=%s: %s",
                record.offset,
                exc,
                exc_info=True,
            )

    def _shutdown(self) -> None:
        """Gracefully close the consumer."""
        logger.info("Shutting down Kafka consumer...")
        if self._consumer:
            try:
                self._consumer.close()
            except KafkaError as exc:
                logger.warning("Error closing consumer: %s", exc)
        logger.info("Kafka consumer stopped.")

    def _register_signal_handlers(self) -> None:
        """Handle SIGTERM and SIGINT for graceful pod shutdown (K8s)."""
        def _handle_signal(signum, frame):
            logger.info("Signal %s received — stopping consumer.", signum)
            self._running = False

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)
