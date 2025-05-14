import re
from django.conf import settings

class CSRFExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf_exempt_urls = [re.compile(url) for url in getattr(settings, 'CSRF_EXEMPT_URLS', [])]

    def __call__(self, request):
        # Mark the request as CSRF exempt if the path matches any exempt URLs
        path = request.path.lstrip('/')
        if any(pattern.match(path) for pattern in self.csrf_exempt_urls):
            request._dont_enforce_csrf_checks = True
            
        response = self.get_response(request)
        return response 