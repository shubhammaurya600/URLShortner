"""
config/settings/base.py

Base Django settings shared across all environments.
Follows 12-factor app principles: all secrets from environment variables.
"""
from pathlib import Path
from decouple import config, Csv

# ─────────────────────────────────────────────────
# Path configuration
# ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────────
# Core security settings
# ─────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())

# ─────────────────────────────────────────────────
# Application definition
# ─────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_prometheus",
]

LOCAL_APPS = [
    "apps.url",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared.middleware.request_id.RequestIdMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────
import dj_database_url  # noqa: E402

DATABASES = {
    "default": dj_database_url.parse(
        config(
            "DATABASE_URL",
            default="postgres://postgres:password@localhost:5432/url_shortener"
        ),
        conn_max_age=600,
        conn_health_checks=True,
    ),
    "replica": dj_database_url.parse(
        config(
            "DATABASE_REPLICA_URL",
            default="postgres://postgres:password@localhost:5432/url_shortener"
        ),
        conn_max_age=600,
        conn_health_checks=True,
    ),
}

DATABASE_ROUTERS = ["shared.db.routers.PrimaryReplicaRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────
# Redis / Cache
# ─────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="rediss://default:gQAAAAAAASFJAAIgcDJjOTJmY2VmYjVlM2E0MzhhYmNlYzE4ZmM1MjJlZWNlMw@chief-donkey-74057.upstash.io:6379")
CACHE_TTL_SECONDS = config("CACHE_TTL_SECONDS", default=86400, cast=int)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 2,
            "SOCKET_TIMEOUT": 2,
            "IGNORE_EXCEPTIONS": True,  # Fail-safe: if Redis is down, fall through to DB
        },
    }
}

# ─────────────────────────────────────────────────
# Kafka
# ─────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = config(
    "KAFKA_BOOTSTRAP_SERVERS", default="kafka:9092"
)
KAFKA_TOPIC_CLICK_EVENTS = config(
    "KAFKA_TOPIC_CLICK_EVENTS", default="url_click_events"
)
KAFKA_CONSUMER_GROUP = config(
    "KAFKA_CONSUMER_GROUP", default="click_analytics_group"
)

# ─────────────────────────────────────────────────
# Application-level config
# ─────────────────────────────────────────────────
BASE_URL = config("BASE_URL", default="http://localhost:8000")
SHORT_CODE_LENGTH = config("SHORT_CODE_LENGTH", default=7, cast=int)
MAX_COLLISION_RETRIES = config("MAX_COLLISION_RETRIES", default=5, cast=int)

# ─────────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────────
THROTTLE_SHORTEN_RATE = config("THROTTLE_SHORTEN_RATE", default="100/min")
THROTTLE_REDIRECT_RATE = config("THROTTLE_REDIRECT_RATE", default="1000/min")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/min",
        "shorten": THROTTLE_SHORTEN_RATE,
        "redirect": THROTTLE_REDIRECT_RATE,
    },
    "EXCEPTION_HANDLER": "shared.exceptions.handlers.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

# ─────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:8080",
    cast=Csv(),
)
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]

# ─────────────────────────────────────────────────
# Password validation
# ─────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────────
# Internationalization
# ─────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────
# Static files
# ─────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ─────────────────────────────────────────────────
# Logging — structured JSON for production use
# ─────────────────────────────────────────────────
LOG_LEVEL = config("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        },
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s %(name)s | %(message)s",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "json_console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "shared": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
