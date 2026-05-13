import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
# Wait, let's just make it load base.py if needed, or development
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.url.services.url_shortener_service import UrlShortenerService
from apps.url.repositories.url_repository import PostgresUrlRepository

repo = PostgresUrlRepository()
service = UrlShortenerService(url_repository=repo)

try:
    url = service.shorten("https://google.com")
    print(f"Success: {url.original_url} -> {url.short_code}")
except Exception as e:
    import traceback
    traceback.print_exc()
