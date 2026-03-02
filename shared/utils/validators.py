"""
shared/utils/validators.py

URL validation utilities.

Key safeguard: SSRF prevention — rejects URLs that resolve to private/loopback
IP ranges, preventing the service from being used as a proxy to internal systems.
"""
import ipaddress
import logging
import socket
from urllib.parse import urlparse

from shared.exceptions.exceptions import InvalidUrlError

logger = logging.getLogger(__name__)

# RFC 1918 + loopback + link-local private ranges
_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

_ALLOWED_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048


def validate_url(url: str) -> str:
    """
    Validate and sanitize a URL.

    Checks performed:
      1. Length guard (max 2048 chars).
      2. Scheme must be http or https.
      3. Hostname must be present.
      4. SSRF guard: resolved IP must not be in private ranges.

    Args:
        url: Raw URL string from request.

    Returns:
        The validated URL (stripped).

    Raises:
        InvalidUrlError: If any check fails.
    """
    url = url.strip()

    if len(url) > _MAX_URL_LENGTH:
        raise InvalidUrlError(f"URL exceeds maximum length of {_MAX_URL_LENGTH} characters.")

    try:
        parsed = urlparse(url)
    except Exception:
        raise InvalidUrlError("Malformed URL.")

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise InvalidUrlError(
            f"URL scheme '{parsed.scheme}' is not allowed. Use http or https."
        )

    hostname = parsed.hostname
    if not hostname:
        raise InvalidUrlError("URL must include a hostname.")

    # SSRF prevention: resolve hostname and check IP
    try:
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
    except (socket.gaierror, ValueError):
        # Cannot resolve — block (safe default)
        raise InvalidUrlError(f"Cannot resolve hostname: {hostname!r}.")

    if _is_private_ip(ip):
        logger.warning("SSRF attempt blocked: hostname=%s ip=%s", hostname, ip_str)
        raise InvalidUrlError("URLs resolving to private/internal IP addresses are not allowed.")

    return url


def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if ip falls within any private IP range."""
    return any(ip in network for network in _PRIVATE_RANGES)


def validate_custom_alias(alias: str) -> str:
    """
    Validate a user-provided custom alias.

    Rules:
      - 3–16 characters.
      - Alphanumeric + hyphens only (no spaces, no special chars).

    Args:
        alias: The proposed alias string.

    Returns:
        Stripped alias.

    Raises:
        InvalidUrlError: If validation fails.
    """
    import re
    alias = alias.strip()
    if not (3 <= len(alias) <= 16):
        raise InvalidUrlError("Custom alias must be between 3 and 16 characters.")
    if not re.match(r"^[a-zA-Z0-9\-]+$", alias):
        raise InvalidUrlError("Custom alias may only contain letters, digits, and hyphens.")
    return alias
