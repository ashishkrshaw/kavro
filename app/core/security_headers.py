from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """adds security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # prevent mime sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # xss protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # force https (hsts) - 2 years
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        # csp - allow swagger ui to work
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
