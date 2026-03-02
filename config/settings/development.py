"""
config/settings/development.py

Development-specific overrides.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# More verbose logging in development
LOGGING["root"]["handlers"] = ["console"]  # type: ignore[name-defined]  # noqa: F405

# Allow all hosts in dev
ALLOWED_HOSTS = ["*"]

# Relaxed CORS in dev
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional, uncomment if installed)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
