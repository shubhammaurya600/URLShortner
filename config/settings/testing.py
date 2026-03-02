"""
config/settings/testing.py

Test settings — uses SQLite in-memory so no PostgreSQL needed for tests.
"""
from .development import *  # noqa: F401, F403

# ─────────────────────────────────────────────────────────
# Use a single SQLite DB for tests (no PostgreSQL needed)
# ─────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    },
    "replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    },
}

# Disable DB router in tests — use "default" for all reads
# (SQLite in-memory DBs can't share tables across connections)
DATABASE_ROUTERS: list = []

# No real Redis in tests — use Django's in-memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable Prometheus in tests (avoids duplicate metric registration)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_prometheus"]  # type: ignore[name-defined] # noqa: F405
MIDDLEWARE = [  # type: ignore[name-defined] # noqa: F405
    mw for mw in MIDDLEWARE  # noqa: F405
    if "prometheus" not in mw.lower()
]

