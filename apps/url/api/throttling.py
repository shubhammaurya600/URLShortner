"""
apps/url/api/throttling.py

Custom DRF throttle classes backed by Redis.

Using named throttles allows different rates for shorten vs redirect.
Named scopes are configured in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
"""
from rest_framework.throttling import AnonRateThrottle


class ShortenRateThrottle(AnonRateThrottle):
    """
    Throttle for POST /api/v1/shorten/ endpoint.
    Rate configured via settings: DEFAULT_THROTTLE_RATES['shorten'].
    Default: 100 requests/minute per IP.
    """
    scope = "shorten"


class RedirectRateThrottle(AnonRateThrottle):
    """
    Throttle for GET /api/v1/<code>/redirect/ endpoint.
    Rate configured via settings: DEFAULT_THROTTLE_RATES['redirect'].
    Default: 1000 requests/minute per IP.
    """
    scope = "redirect"
