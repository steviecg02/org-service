"""
Authentication routes for Google OAuth login and callback.
Phase 1: Minimal implementation (no database).
"""

from authlib.common.security import generate_token  # type: ignore[import-untyped]
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.responses import RedirectResponse

from org_service.config import settings
from org_service.schemas.auth import TokenResponse
from org_service.services.auth_service import handle_google_callback, oauth

# Initialize rate limiter for auth routes
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        429: {"description": "Rate limit exceeded (10 requests/minute)"},
    },
)


@router.get("/login", response_class=RedirectResponse)
@limiter.limit("10/minute")
async def login(request: Request) -> RedirectResponse:
    """
    Redirects to Google OAuth login.

    Initiates the OAuth flow by redirecting the user to Google's consent screen.

    Args:
        request: FastAPI request object

    Returns:
        RedirectResponse: Redirect to Google OAuth consent screen
    """
    nonce = generate_token()
    request.session["nonce"] = nonce

    return await oauth.google.authorize_redirect(  # type: ignore[no-any-return]
        request,
        settings.google_oauth_redirect_uri,
        nonce=nonce,
    )


@router.get("/callback", response_model=TokenResponse)
@limiter.limit("10/minute")
async def auth_callback(request: Request) -> TokenResponse:
    """
    Handles the OAuth callback from Google and returns JWT.

    Phase 1: No database - just extract Google user info and generate JWT
    with hardcoded org_id and is_owner=True.

    Args:
        request: FastAPI request with OAuth callback parameters

    Returns:
        TokenResponse: JWT access token and token type

    Raises:
        HTTPException: 400 if OAuth state is invalid or user info incomplete
    """
    jwt_token = await handle_google_callback(request)
    return TokenResponse(access_token=jwt_token, token_type="bearer")  # nosec B106
