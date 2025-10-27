"""
Authentication-related Pydantic schemas.
"""

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    OAuth callback response containing JWT access token.

    Phase 1: Returns JWT with hardcoded org_id and is_owner=True.
    """

    access_token: str = Field(..., description="JWT access token for API authentication")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    }
