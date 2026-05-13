---
title: URL Shortener API
emoji: 🔗
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
---

# URL Shortener — Backend API

A production-ready URL shortener backend built with Django + Django REST Framework.

## Features
- Shorten URLs with optional custom aliases and expiry
- Redis caching for ultra-fast redirects
- Click analytics
- QR code generation
- Rate limiting

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/shorten/` | Shorten a URL |
| `GET` | `/api/v1/<code>/redirect/` | Redirect to original URL |
| `GET` | `/api/v1/<code>/analytics/` | Get click analytics |
| `GET` | `/api/v1/<code>/qrcode/` | Get QR code PNG |
| `GET` | `/health/` | Health check |

## Environment Variables (Secrets)

Set these in your Space **Settings → Repository secrets**:

- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection string
- `DATABASE_REPLICA_URL` — Replica DB (can be same as `DATABASE_URL`)
- `REDIS_URL` — Redis connection string
- `ALLOWED_HOSTS` — Comma-separated allowed hosts
- `CORS_ALLOWED_ORIGINS` — Comma-separated allowed CORS origins
- `BASE_URL` — Public URL of this Space
- `DEBUG` — `False` for production
