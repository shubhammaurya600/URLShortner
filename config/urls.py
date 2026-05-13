"""
config/urls.py — Root URL configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def root_health_check(request):
    return HttpResponse("URL Shortener API is running.", status=200)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.url.api.urls")),
    path("", include("django_prometheus.urls")),
    path("", root_health_check, name="root"),
]
