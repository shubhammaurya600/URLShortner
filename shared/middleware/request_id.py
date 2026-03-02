"""
shared/middleware/request_id.py

Injects a unique request_id into every request so that all log lines
emitted during that request share the same ID — critical for distributed
tracing and log correlation.

Usage in settings:
    MIDDLEWARE += ["shared.middleware.request_id.RequestIdMiddleware"]
"""
import logging
import uuid

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-Id"
REQUEST_ID_ATTR = "request_id"


class RequestIdMiddleware:
    """
    Adds a unique ``request_id`` to every request.

    Priority:
        1. Use the incoming ``X-Request-Id`` header (propagated by load balancer).
        2. Generate a new UUID4 if the header is absent.

    The request_id is:
        - Attached to ``request.request_id`` for access in views.
        - Set in the response header ``X-Request-Id``.
        - Injected into the ``logging.LoggerAdapter`` extra so all logs
          during this request carry it automatically.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(
            f"HTTP_{REQUEST_ID_HEADER.upper().replace('-', '_')}",
            str(uuid.uuid4()),
        )
        request.request_id = request_id  # type: ignore[attr-defined]

        # Inject into the logging system via a LogRecord factory override
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record

        logging.setLogRecordFactory(record_factory)

        response = self.get_response(request)

        # Restore factory to avoid leaking state between requests in same thread
        logging.setLogRecordFactory(old_factory)

        response[REQUEST_ID_HEADER] = request_id
        return response
