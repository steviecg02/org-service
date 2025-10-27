"""
Handles Google OAuth login and JWT generation.
Phase 1: Minimal implementation (no database, hardcoded values).
"""

# fmt: off
from authlib.integrations.base_client.errors import (
    MismatchingStateError,  # type: ignore[import-untyped]
)
from authlib.integrations.starlette_client import OAuth  # type: ignore[import-untyped]

# fmt: on
from fastapi import HTTPException
from starlette.requests import Request

from org_service.config import logger, settings
from org_service.utils.jwt import create_jwt_token

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def handle_google_callback(request: Request) -> str:
    """
    Handles OAuth callback and returns JWT with hardcoded values.

    Phase 1: No database, no user/account creation. Just extract Google user info
    and generate JWT with hardcoded org_id and is_owner=True.

    Args:
        request (Request): Incoming FastAPI request.

    Returns:
        str: JWT access token.

    Raises:
        HTTPException: If OAuth state is invalid or user info is incomplete.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except MismatchingStateError:
        logger.warning("OAuth callback failed: mismatching state")
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from None

    nonce = request.session.get("nonce")
    userinfo = await oauth.google.parse_id_token(token, nonce)

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")

    if not all([google_sub, email]):
        logger.error("Incomplete user info from Google")
        raise HTTPException(status_code=400, detail="Invalid Google response")

    logger.info(f"User logged in via Google: {email}")

    # Phase 1: Hardcoded values - no database lookup
    token_data = {
        "sub": google_sub,  # Google user ID
        "org_id": settings.hardcoded_org_id,  # Hardcoded org ID
        "email": email,
        "is_owner": True,  # Everyone is owner in Phase 1
    }

    return create_jwt_token(token_data)
