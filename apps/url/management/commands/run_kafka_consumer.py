"""
apps/url/management/commands/run_kafka_consumer.py

Django management command to start the Kafka consumer worker.

Usage:
    python manage.py run_kafka_consumer
    python manage.py run_kafka_consumer --topic=custom_topic --group=custom_group

In production / Kubernetes:
    Deploy as a separate Deployment (not part of the Django API pods).
    Scale by adding more replicas — Kafka distributes partitions across the group.
"""
import logging

from django.core.management.base import BaseCommand

from apps.url.infrastructure.kafka_consumer import ClickEventConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start the Kafka consumer worker for processing URL click events."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--topic",
            type=str,
            default=None,
            help="Kafka topic to consume (default: from settings).",
        )
        parser.add_argument(
            "--group",
            type=str,
            default=None,
            help="Kafka consumer group ID (default: from settings).",
        )
        parser.add_argument(
            "--servers",
            type=str,
            default=None,
            help="Kafka bootstrap servers (default: from settings).",
        )

    def handle(self, *args, **options) -> None:
        self.stdout.write(
            self.style.SUCCESS("Starting Kafka click event consumer...")
        )

        consumer = ClickEventConsumer(
            bootstrap_servers=options.get("servers"),
            topic=options.get("topic"),
            group_id=options.get("group"),
        )

        try:
            consumer.start()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Consumer stopped by user."))
        except Exception as exc:
            logger.exception("Consumer crashed: %s", exc)
            self.stderr.write(self.style.ERROR(f"Consumer error: {exc}"))
            raise SystemExit(1)
