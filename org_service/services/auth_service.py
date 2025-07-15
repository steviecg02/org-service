"""
Handles Google OAuth login, user creation, and JWT generation.
"""

from authlib.integrations.base_client.errors import MismatchingStateError
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import AsyncGenerator

from org_service.db import async_session_maker
from org_service.config import settings
from org_service.logging_config import logger
from org_service.models import User, Account
from org_service.utils.jwt import create_jwt_token

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency to provide a database session.
    """
    async with async_session_maker() as session:
        yield session


async def handle_google_callback(request: Request, db: AsyncSession) -> str:
    """
    Handles OAuth callback, creates user/account if new, returns JWT.

    Args:
        request (Request): Incoming FastAPI request.
        db (AsyncSession): SQLAlchemy async session.

    Returns:
        str: JWT access token.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except MismatchingStateError:
        logger.warning("OAuth callback failed: mismatching state")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    nonce = request.session.get("nonce")
    userinfo = await oauth.google.parse_id_token(token, nonce)

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")

    if not all([google_sub, email, name]):
        logger.error("Incomplete user info from Google")
        raise HTTPException(status_code=400, detail="Invalid Google response")

    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if not user:
        account = Account()
        db.add(account)
        await db.flush()

        user = User(
            google_sub=google_sub,
            email=email,
            full_name=name,
            account_id=account.account_id,
        )
        db.add(user)
        await db.commit()

        logger.info(f"Created new user: {email}")
    else:
        logger.info(f"Existing user found: {email}")

    token_data = {
        "sub": str(user.user_id),
        "account_id": str(user.account_id),
        "roles": ["owner"],  # TODO: Replace with actual role resolution
        "email": user.email,
    }

    return create_jwt_token(token_data)
