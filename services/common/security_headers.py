from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects mandatory HTTP security headers into all responses:
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    - Strict-Transport-Security
    - X-XSS-Protection
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; " "script-src 'self'; " "style-src 'self' 'unsafe-inline'; " "img-src 'self' data:; " "font-src 'self'; " "object-src 'none'; " "frame-ancestors 'none'"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
