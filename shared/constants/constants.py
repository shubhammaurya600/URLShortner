"""
shared/constants/constants.py

Application-wide constants. Centralised so they never scatter across files.
Import individual names, not the module, to enable easier refactoring.
"""

# ─────────────────────────────────────────────────
# Redis key templates
# ─────────────────────────────────────────────────
# Used by RedisCache to build and parse cache keys.
REDIS_URL_KEY_PREFIX = "short_url"  # full key: short_url:{short_code}

# ─────────────────────────────────────────────────
# Kafka
# ─────────────────────────────────────────────────
KAFKA_TOPIC_CLICK_EVENTS = "url_click_events"
KAFKA_DELIVERY_TIMEOUT_MS = 5_000   # producer: fail-fast timeout
KAFKA_REQUEST_TIMEOUT_MS = 3_000

# ─────────────────────────────────────────────────
# Short code generation
# ─────────────────────────────────────────────────
DEFAULT_SHORT_CODE_LENGTH = 7
MAX_COLLISION_RETRIES = 5
COLLISION_SALT_PREFIX = "retry"

# ─────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────
DEFAULT_CACHE_TTL_SECONDS = 86_400  # 24 hours

# ─────────────────────────────────────────────────
# URL metadata
# ─────────────────────────────────────────────────
MAX_URL_LENGTH = 2048
MAX_ALIAS_LENGTH = 16
MIN_ALIAS_LENGTH = 3

# ─────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────
ANALYTICS_CLICK_WINDOW_DAYS = 30  # raw click events retained this long
