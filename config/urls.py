"""
config/urls.py — Root URL configuration.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.url.api.urls")),
    path("", include("django_prometheus.urls")),
]
