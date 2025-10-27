"""
Middleware to generate and inject request IDs for distributed tracing.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generates a unique request ID for each request and adds it to response headers.

    The request ID can be used for distributed tracing and log correlation.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """
        Process the request and add request ID to headers.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store request ID in request state for access in routes
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
