"""
Middleware to validate JWT tokens and inject user context into requests.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from typing import Optional
from ..config import settings
from ..logging_config import logger


class JWTMiddleware(BaseHTTPMiddleware):
    """
    Validates Authorization header and attaches user context to request.state.
    """

    def __init__(self, app, exempt_paths: Optional[list[str]] = None):
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
            request.state.user = {
                "user_id": payload["sub"],
                "account_id": payload["account_id"],
                "email": payload["email"],
                "roles": payload["roles"],
            }
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)
