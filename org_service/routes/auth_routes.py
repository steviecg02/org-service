"""
Authentication routes for login and callback endpoints.
"""

from authlib.common.security import generate_token
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from ..services.auth_service import oauth, handle_google_callback, get_db
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """
    Redirects to Google OAuth login.
    """
    nonce = generate_token()
    request.session["nonce"] = nonce

    response = await oauth.google.authorize_redirect(
        request,
        settings.google_oauth_redirect_uri,
        nonce=nonce,
    )

    return response


@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles the OAuth callback, creates user, returns JWT.

    Returns:
        dict: { access_token, token_type }
    """
    jwt_token = await handle_google_callback(request, db)
    return {"access_token": jwt_token, "token_type": "bearer"}
