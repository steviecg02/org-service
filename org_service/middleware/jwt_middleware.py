"""
Middleware to validate JWT tokens and inject user context into requests.
Phase 1: Simplified for org_id instead of account_id.
"""

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from org_service.config import logger, settings


class JWTMiddleware(BaseHTTPMiddleware):
    """
    Validates Authorization header and attaches user context to request.state.

    Phase 1: JWT contains org_id (hardcoded) and is_owner instead of account_id/roles.
    """

    def __init__(self, app, exempt_paths: list[str] | None = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or []

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            # Phase 1: Store Google user ID, org_id, email, is_owner
            request.state.user = {
                "google_sub": payload["sub"],  # Google user ID
                "org_id": payload["org_id"],
                "email": payload["email"],
                "is_owner": payload.get("is_owner", True),
            }
        except JWTError as e:
            logger.warning(
                "JWT validation failed",
                extra={"error": str(e), "path": request.url.path},
            )
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)
