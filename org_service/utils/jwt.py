"""
JWT utility functions for token creation and decoding.

Used to issue and verify authentication tokens within the system.
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from jose import jwt

from org_service.config import settings


def create_jwt_token(
    data: dict, expiry_seconds: int = settings.jwt_expiry_seconds
) -> str:
    """
    Create a JWT token with the given payload and optional expiration.

    Args:
        data (dict): Payload to encode. Must include:
            - 'sub': str (user ID)
            - 'account_id': str (account ID)
            - 'roles': List[str] (optional roles)
        expiry_seconds (int, optional): Expiration in seconds. Defaults to settings.jwt_expiry_seconds.

    Returns:
        str: Encoded JWT token
    """
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expiry_seconds)
    payload["exp"] = expire
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token into its claims.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Dict[str, Any]: The decoded token payload.

    Raises:
        jose.JWTError: If the token is invalid or expired.
    """
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
