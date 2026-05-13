import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import RequestFactory
from apps.url.api.views import ShortenUrlView

factory = RequestFactory()
request = factory.post('/api/v1/shorten/', {"original_url": "https://bing.com"}, content_type='application/json')

view = ShortenUrlView.as_view()

try:
    response = view(request)
    print(f"Status Code: {response.status_code}")
    print(response.rendered_content if hasattr(response, 'rendered_content') else response.data)
except Exception as e:
    import traceback
    traceback.print_exc()
