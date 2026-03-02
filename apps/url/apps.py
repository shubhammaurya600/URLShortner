"""
apps/url/apps.py
"""
from django.apps import AppConfig


class UrlConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.url"
    label = "url"
    verbose_name = "URL Shortener"
