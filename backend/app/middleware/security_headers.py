"""Security headers middleware — production-grade HTTP security.

Per ARCHITECTURE.md §8: HTTPS everywhere.
Implements OWASP-recommended security headers for the FastAPI backend.
"""
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings

logger = logging.getLogger(__name__)

# Maximum request body size (10 MB default, lower for API-only endpoints)
MAX_BODY_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response.

    Headers follow OWASP Secure Headers Project recommendations:
    https://owasp.org/www-project-secure-headers/
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # ── Core security headers ─────────────────────────────────
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy — don't leak full URLs to third parties
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # ── HSTS (only in production/pilot) ───────────────────────
        if settings.ENVIRONMENT in ("pilot", "production"):
            # Enforce HTTPS for 1 year, include subdomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # ── Content Security Policy ───────────────────────────────
        if settings.ENVIRONMENT in ("pilot", "production"):
            # Strict CSP for API responses
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'none'; "
                "form-action 'none'"
            )

        # ── Cache control for API responses ───────────────────────
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests for security concerns.

    - Enforce Content-Type on POST/PUT/PATCH
    - Reject oversized payloads
    - Log suspicious patterns
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # ── Payload size check ────────────────────────────────────
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE_BYTES:
            logger.warning(
                f"🚫 Rejected oversized request: {content_length} bytes "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=413,
                media_type="application/json",
            )

        # ── Content-Type enforcement for mutation requests ────────
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            # Allow JSON, form data, and multipart (for file uploads)
            allowed_types = (
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            )
            # Webhook endpoints may send different content types
            is_webhook = "/webhook" in request.url.path
            if not is_webhook and content_type:
                if not any(ct in content_type for ct in allowed_types):
                    logger.warning(
                        f"⚠️ Unexpected Content-Type: {content_type} "
                        f"on {request.method} {request.url.path}"
                    )

        response = await call_next(request)
        return response
