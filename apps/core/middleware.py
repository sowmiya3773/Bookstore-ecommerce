"""Core middleware for rate limiting and security."""

import time
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings
from functools import wraps

class RateLimitMiddleware:
    """Rate limiting middleware to prevent abuse."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if settings.RATE_LIMIT_ENABLED:
            # Get client IP
            ip = self.get_client_ip(request)
            
            # Get rate limit based on authentication
            if request.user.is_authenticated:
                rate_limit = settings.RATE_LIMIT_USER
            else:
                rate_limit = settings.RATE_LIMIT_ANON
            
            # Parse rate limit
            limit, period = self._parse_rate_limit(rate_limit)
            
            # Check rate limit
            cache_key = f'rate_limit_{ip}'
            request_count = cache.get(cache_key, 0)
            
            if request_count >= limit:
                return HttpResponse('Rate limit exceeded', status=429)
            
            # Increment counter
            cache.set(cache_key, request_count + 1, period)
        
        response = self.get_response(request)
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _parse_rate_limit(rate_limit_str):
        """Parse rate limit string like '100/hour'."""
        if '/' not in rate_limit_str:
            return 100, 3600
        
        limit, period_str = rate_limit_str.split('/')
        limit = int(limit)
        
        periods = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400,
        }
        
        period = periods.get(period_str, 3600)
        return limit, period


def rate_limit(limit_string='100/hour'):
    """Decorator for rate limiting views."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            ip = RateLimitMiddleware.get_client_ip(request)
            limit, period = RateLimitMiddleware._parse_rate_limit(limit_string)
            
            cache_key = f'view_rate_limit_{ip}_{view_func.__name__}'
            request_count = cache.get(cache_key, 0)
            
            if request_count >= limit:
                return HttpResponse('Rate limit exceeded', status=429)
            
            cache.set(cache_key, request_count + 1, period)
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
