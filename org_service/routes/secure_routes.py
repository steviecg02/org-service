"""
Protected routes that require JWT authentication.
Phase 1: Simple whoami endpoint.
"""

from fastapi import APIRouter, Request

from org_service.config import logger
from org_service.schemas.user import UserContext, WhoAmIResponse

router = APIRouter(
    prefix="/secure",
    tags=["Protected"],
    responses={
        401: {"description": "Unauthorized - Missing or invalid JWT token"},
    },
)


@router.get("/whoami", response_model=WhoAmIResponse)
async def whoami(request: Request) -> WhoAmIResponse:
    """
    Returns current user context from JWT.

    Phase 1: Returns Google user ID, org_id, email, is_owner.

    Args:
        request: FastAPI request with user context attached by JWT middleware

    Returns:
        WhoAmIResponse: User information from JWT payload
    """
    logger.info(
        "User accessed whoami endpoint",
        extra={
            "email": request.state.user.get("email"),
            "org_id": request.state.user.get("org_id"),
        },
    )
    user_context = UserContext(**request.state.user)
    return WhoAmIResponse(user=user_context)
