"""
JWT utility functions for token creation and decoding.

Phase 1: Minimal implementation for Google OAuth + JWT (no database).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from org_service.config import settings


def create_jwt_token(data: dict, expiry_seconds: int = settings.jwt_expiry_seconds) -> str:
    """
    Create a JWT token with the given payload and optional expiration.

    Phase 1: Hardcoded org_id and is_owner=True for all users.

    Args:
        data (dict): Payload to encode. Must include:
            - 'sub': str (Google user ID)
            - 'email': str (user email)
        expiry_seconds (int, optional): Expiration in seconds. Defaults to 7 days.

    Returns:
        str: Encoded JWT token
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT token into its claims.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Dict[str, Any]: The decoded token payload.

    Raises:
        jose.JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
