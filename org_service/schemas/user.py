"""
User-related Pydantic schemas.
"""

from pydantic import BaseModel, EmailStr, Field


class UserContext(BaseModel):
    """
    User context extracted from JWT token.

    Phase 1: Contains Google user ID, org_id, email, and is_owner flag.
    """

    google_sub: str = Field(..., description="Google user ID (sub claim)")
    org_id: str = Field(..., description="Organization ID (hardcoded in Phase 1)")
    email: EmailStr = Field(..., description="User's email address")
    is_owner: bool = Field(
        default=True, description="Whether user is org owner (always True in Phase 1)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "google_sub": "google-user-12345",
                "org_id": "11111111-1111-1111-1111-111111111111",
                "email": "user@example.com",
                "is_owner": True,
            }
        }
    }


class WhoAmIResponse(BaseModel):
    """
    Response from /secure/whoami endpoint.

    Returns the current authenticated user's context.
    """

    user: UserContext = Field(..., description="Current user context from JWT")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "google_sub": "google-user-12345",
                    "org_id": "11111111-1111-1111-1111-111111111111",
                    "email": "user@example.com",
                    "is_owner": True,
                }
            }
        }
    }
