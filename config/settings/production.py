"""
config/settings/production.py

Production-specific settings — security hardened, JSON logging.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# ─────────────────────────────────────────────────
# Security hardening
# ─────────────────────────────────────────────────
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# ─────────────────────────────────────────────────
# JSON logging for production (structured / ELK / Splunk friendly)
# ─────────────────────────────────────────────────
LOGGING["root"]["handlers"] = ["json_console"]  # type: ignore[name-defined]  # noqa: F405
LOGGING["loggers"]["apps"]["handlers"] = ["json_console"]  # type: ignore[name-defined]  # noqa: F405
LOGGING["loggers"]["shared"]["handlers"] = ["json_console"]  # type: ignore[name-defined]  # noqa: F405
