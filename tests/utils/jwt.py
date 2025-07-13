from org_service.utils.jwt import create_jwt_token as real_create_jwt_token


def create_jwt_token(user, expiry_seconds=None):
    """Wraps real JWT token creator to safely use a User object."""
    payload = {
        "sub": str(user.user_id),
        "email": user.email,
        "account_id": str(user.account_id),
        "full_name": user.full_name or "",
    }
    return real_create_jwt_token(payload, expiry_seconds=expiry_seconds)
