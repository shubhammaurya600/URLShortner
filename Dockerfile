# ─────────────────────────────────────────────────────────────────────────────
# URL Shortener — Multi-stage Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Build dependencies (separate from runtime for smaller final image)
# Stage 2: Runtime image (non-root, minimal attack surface)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install only what's needed to build psycopg2 and other C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Production runtime
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Runtime-only system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user (principle of least privilege)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=appuser:appuser . .

# Collect static files (WhiteNoise serves them)
RUN python manage.py collectstatic --noinput --settings=config.settings.production 2>/dev/null || true

USER appuser

EXPOSE ${PORT:-8000}

# Gunicorn with sensible production defaults:
#   - 4 workers (2 * CPU + 1 is common heuristic; override via ENV in K8s)
#   - 120s timeout
#   - Access log to stdout for container log aggregation
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class sync --timeout 120 --access-logfile - --error-logfile - config.wsgi:application
