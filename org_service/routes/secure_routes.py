from fastapi import APIRouter, Request

router = APIRouter(prefix="/secure", tags=["secure"])


@router.get("/whoami")
async def whoami(request: Request):
    """
    Returns current user context from JWT.
    """
    print("👤 request.state.user:", request.state.user)
    return {"user": request.state.user}
