"""
apps/url/admin.py

Django Admin customization for the URL Shortener.

Provides a rich admin UI with search, filters, list display,
and custom actions for URL management.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.url.models import ClickEventModel, UrlModel


@admin.register(UrlModel)
class UrlModelAdmin(admin.ModelAdmin):
    """Admin panel for shortened URLs."""

    list_display = [
        "short_code",
        "truncated_original_url",
        "is_active",
        "created_at",
        "expires_at",
        "click_count_display",
    ]
    list_filter = ["is_active", "created_at", "expires_at"]
    search_fields = ["short_code", "original_url"]
    readonly_fields = ["created_at", "short_code"]
    ordering = ["-created_at"]
    list_per_page = 50

    actions = ["deactivate_urls", "activate_urls"]

    @admin.display(description="Original URL")
    def truncated_original_url(self, obj: UrlModel) -> str:
        url = obj.original_url
        if len(url) > 60:
            url = url[:57] + "..."
        return format_html('<a href="{}" target="_blank">{}</a>', obj.original_url, url)

    @admin.display(description="Clicks")
    def click_count_display(self, obj: UrlModel) -> int:
        return ClickEventModel.objects.filter(short_code=obj.short_code).count()

    @admin.action(description="Deactivate selected URLs")
    def deactivate_urls(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} URL(s) deactivated.")

    @admin.action(description="Activate selected URLs")
    def activate_urls(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} URL(s) activated.")


@admin.register(ClickEventModel)
class ClickEventModelAdmin(admin.ModelAdmin):
    """Admin panel for click events (read-only analytics view)."""

    list_display = [
        "short_code",
        "clicked_at",
        "ip_address",
        "user_agent_truncated",
    ]
    list_filter = ["clicked_at", "short_code"]
    search_fields = ["short_code", "ip_address"]
    readonly_fields = [
        "event_id",
        "short_code",
        "clicked_at",
        "ip_address",
        "user_agent",
        "metadata",
    ]
    ordering = ["-clicked_at"]
    list_per_page = 100

    def has_add_permission(self, request) -> bool:
        return False  # Click events are created by the Kafka consumer only

    def has_change_permission(self, request, obj=None) -> bool:
        return False  # Read-only

    @admin.display(description="User Agent")
    def user_agent_truncated(self, obj: ClickEventModel) -> str:
        if not obj.user_agent:
            return "—"
        ua = obj.user_agent
        return ua[:60] + "..." if len(ua) > 60 else ua
