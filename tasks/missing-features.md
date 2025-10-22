# Missing Features

Features mentioned in README or implied by architecture but not yet implemented.

---

## 1. Service-to-Service Authentication

**Status:** Not Implemented
**Pattern:** See SECURITY-PATTERNS.md Pattern 3
**Priority:** P1 (needed for microservice architecture)

**Use Case:**
Other microservices (sync-hostaway, sync-airbnb) need to call org-service APIs to validate JWTs, get user info, check permissions.

**Implementation:**

### Create Service API Keys
```python
# models/service_api_key.py
class ServiceAPIKey(Base):
    """API key for service-to-service authentication."""
    __tablename__ = "service_api_keys"

    key_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String, nullable=False, unique=True)
    api_key_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
```

### Service Authentication Middleware
```python
# middleware/service_auth.py
class ServiceAuthMiddleware:
    """Authenticate service-to-service requests."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/internal/"):
            # Require X-Service-Key header
            api_key = request.headers.get("X-Service-Key")
            if not await validate_service_key(api_key):
                return JSONResponse(status_code=401, content={"detail": "Invalid service key"})

        return await call_next(request)
```

### Internal Endpoints
```python
# routes/internal_routes.py
@router.post("/internal/validate-jwt")
async def validate_jwt_for_service(token: str):
    """Validate JWT and return user context (service-to-service only)."""
    try:
        payload = decode_jwt_token(token)
        return {"valid": True, "user": payload}
    except JWTError:
        return {"valid": False, "error": "Invalid token"}

@router.get("/internal/user/{user_id}")
async def get_user_for_service(user_id: str, account_id: str):
    """Get user details (service-to-service only)."""
    # Query user with account_id filter
    ...
```

**Estimated Time:** 8-10 hours

---

## 2. Refresh Tokens

**Status:** Not Implemented
**Pattern:** See SECURITY-PATTERNS.md Pattern 6
**Priority:** P2 (nice to have for mobile apps)

**Use Case:**
- Mobile apps need long-lived sessions
- Reduce frequency of OAuth re-authentication
- Improve security (short-lived access tokens)

**Implementation:**

### Create Refresh Token Table
```python
# models/refresh_token.py
class RefreshToken(Base):
    """Refresh tokens for long-lived sessions."""
    __tablename__ = "refresh_tokens"

    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_revoked = Column(Boolean, default=False)
```

### Issue Refresh Token on Login
```python
# services/auth_service.py
async def handle_google_callback(...):
    # ... existing code ...

    # Create access token (short-lived: 1 hour)
    access_token = create_jwt_token(token_data, expiry_seconds=3600)

    # Create refresh token (long-lived: 30 days)
    refresh_token = await create_refresh_token(user.user_id, user.account_id, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600
    }
```

### Refresh Endpoint
```python
# routes/auth_routes.py
@router.post("/refresh")
async def refresh_access_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """
    Exchange refresh token for new access token.

    Args:
        refresh_token: Valid refresh token
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: 401 if refresh token invalid/expired
    """
    # Verify refresh token
    token_record = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
    )
    token = token_record.scalar_one_or_none()

    if not token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Get user
    user = await db.execute(select(User).where(User.user_id == token.user_id))
    user = user.scalar_one()

    # Get roles
    roles_result = await db.execute(
        select(UserRole.role_name).where(
            UserRole.user_id == user.user_id,
            UserRole.account_id == user.account_id
        )
    )
    roles = [row[0] for row in roles_result.fetchall()]

    # Create new access token
    access_token = create_jwt_token({
        "sub": str(user.user_id),
        "account_id": str(user.account_id),
        "email": user.email,
        "roles": roles
    }, expiry_seconds=3600)

    # Update last_used_at
    token.last_used_at = datetime.utcnow()
    await db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }
```

**Estimated Time:** 6-8 hours

---

## 3. Microsoft OAuth

**Status:** Not Implemented
**Priority:** P3 (requested in README)

**Implementation:**

### Add to services/auth_service.py
```python
# Register Microsoft OAuth
oauth.register(
    name="microsoft",
    client_id=settings.microsoft_client_id,
    client_secret=settings.microsoft_client_secret,
    server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)
```

### Add Routes
```python
# routes/auth_routes.py
@router.get("/login/microsoft")
async def login_microsoft(request: Request):
    """Redirect to Microsoft OAuth login."""
    redirect_uri = settings.microsoft_oauth_redirect_uri
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@router.get("/callback/microsoft")
async def microsoft_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Microsoft OAuth callback."""
    token = await oauth.microsoft.authorize_access_token(request)
    userinfo = await oauth.microsoft.parse_id_token(token)

    # Same logic as Google callback
    microsoft_sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")

    # Find or create user
    ...
```

### Update User Model
```python
# models/user.py
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...
    google_sub = Column(String, unique=True, nullable=True)
    microsoft_sub = Column(String, unique=True, nullable=True)  # Add this
```

**Estimated Time:** 4-6 hours

---

## 4. Email/Password Authentication

**Status:** Not Implemented
**Priority:** P3 (fallback for non-OAuth users)

**Implementation:**

### Update User Model
```python
# models/user.py
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...
    password_hash = Column(String, nullable=True)  # Uncomment this
```

### Create Password Hashing Utility
```python
# utils/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### Registration Endpoint
```python
# routes/auth_routes.py
from org_service.schemas import UserCreate
from org_service.utils.password import hash_password

@router.post("/register")
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user with email/password.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        JWT token

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create account and user
    account = Account()
    db.add(account)
    await db.flush()

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
        account_id=account.account_id
    )
    db.add(user)
    await db.commit()

    # Issue JWT
    token = create_jwt_token({
        "sub": str(user.user_id),
        "account_id": str(user.account_id),
        "email": user.email,
        "roles": ["owner"]
    })

    return {"access_token": token, "token_type": "bearer"}
```

### Login Endpoint
```python
@router.post("/login/password")
async def login_with_password(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email/password.

    Args:
        email: User email
        password: User password
        db: Database session

    Returns:
        JWT token

    Raises:
        HTTPException: 401 if invalid credentials
    """
    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Get roles
    roles_result = await db.execute(
        select(UserRole.role_name).where(
            UserRole.user_id == user.user_id,
            UserRole.account_id == user.account_id
        )
    )
    roles = [row[0] for row in roles_result.fetchall()]

    # Issue JWT
    token = create_jwt_token({
        "sub": str(user.user_id),
        "account_id": str(user.account_id),
        "email": user.email,
        "roles": roles
    })

    return {"access_token": token, "token_type": "bearer"}
```

**Dependencies:**
```
passlib[bcrypt]
```

**Estimated Time:** 6-8 hours

---

## 5. Invite-Based Account Joining

**Status:** Not Implemented
**Priority:** P2 (important for team collaboration)

**Use Case:**
- Account owner invites new users to join existing account
- Invited user signs up and gets "member" role (not "owner")

**Implementation:**

### Create Invite Table
```python
# models/invite.py
class Invite(Base):
    """Invitation to join an account."""
    __tablename__ = "invites"

    invite_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False)
    invited_email = Column(String, nullable=False)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    invite_token = Column(String, nullable=False, unique=True)
    role_name = Column(String, default="member")
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

### Create Invite Endpoint
```python
# routes/invite_routes.py
@router.post("/invites")
@require_role(["admin", "owner"])
async def create_invite(
    email: str,
    role: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create invite for user to join account.

    Args:
        email: Email of user to invite
        role: Role to assign (member, admin)
        request: Request with user context
        db: Database session

    Returns:
        Invite details with token

    Raises:
        HTTPException: 403 if not admin/owner
    """
    account_id = request.state.user["account_id"]
    invited_by = request.state.user["user_id"]

    # Generate unique token
    invite_token = secrets.token_urlsafe(32)

    # Create invite (expires in 7 days)
    invite = Invite(
        account_id=account_id,
        invited_email=email,
        invited_by_user_id=invited_by,
        invite_token=invite_token,
        role_name=role,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(invite)
    await db.commit()

    # Send invite email (TODO: implement email service)
    invite_url = f"{settings.app_url}/auth/accept-invite?token={invite_token}"

    return {
        "invite_id": str(invite.invite_id),
        "invite_url": invite_url,
        "expires_at": invite.expires_at.isoformat()
    }
```

### Accept Invite
```python
@router.post("/auth/accept-invite")
async def accept_invite(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept invite and join account.

    Requires user to be logged in. Adds user to invited account.

    Args:
        token: Invite token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 400 if token invalid/expired
        HTTPException: 401 if not authenticated
    """
    # Verify invite
    result = await db.execute(
        select(Invite).where(
            Invite.invite_token == token,
            Invite.accepted_at == None,
            Invite.expires_at > datetime.utcnow()
        )
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invite")

    # User must be logged in
    # Get user_id from JWT (requires JWT middleware)
    # Or: Redirect to OAuth login with invite token preserved

    # Add user to account with specified role
    user_role = UserRole(
        user_id=current_user_id,
        account_id=invite.account_id,
        role_name=invite.role_name
    )
    db.add(user_role)

    # Mark invite as accepted
    invite.accepted_at = datetime.utcnow()
    await db.commit()

    return {"status": "accepted", "account_id": str(invite.account_id)}
```

**Estimated Time:** 8-10 hours

---

## 6. Password Reset Flow

**Status:** Not Implemented
**Priority:** P3 (needed if email/password auth implemented)

**Implementation:**

### Create Password Reset Table
```python
# models/password_reset.py
class PasswordReset(Base):
    """Password reset tokens."""
    __tablename__ = "password_resets"

    reset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    reset_token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

### Request Reset
```python
@router.post("/auth/forgot-password")
async def request_password_reset(email: str, db: AsyncSession = Depends(get_db)):
    """
    Request password reset email.

    Args:
        email: User email
        db: Database session

    Returns:
        Success message (always, to prevent email enumeration)
    """
    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user and user.password_hash:  # Only for email/password users
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)

        # Create reset record
        reset = PasswordReset(
            user_id=user.user_id,
            reset_token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset)
        await db.commit()

        # Send email (TODO: implement email service)
        reset_url = f"{settings.app_url}/reset-password?token={reset_token}"

    # Always return success (prevent email enumeration)
    return {"status": "ok", "message": "If email exists, reset link sent"}
```

### Reset Password
```python
@router.post("/auth/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token.

    Args:
        token: Reset token from email
        new_password: New password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 400 if token invalid/expired
    """
    # Verify token
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.reset_token == token,
            PasswordReset.used_at == None,
            PasswordReset.expires_at > datetime.utcnow()
        )
    )
    reset = result.scalar_one_or_none()

    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Update password
    user_result = await db.execute(select(User).where(User.user_id == reset.user_id))
    user = user_result.scalar_one()

    user.password_hash = hash_password(new_password)

    # Mark token as used
    reset.used_at = datetime.utcnow()

    await db.commit()

    return {"status": "ok", "message": "Password reset successful"}
```

**Estimated Time:** 4-6 hours (without email service)

---

## Summary

**Total Estimated Time for All Missing Features:** 40-60 hours

**Recommended Implementation Order:**
1. Service-to-service auth (P1) - Needed for microservices
2. Invite system (P2) - Enables team collaboration
3. Refresh tokens (P2) - Improves mobile UX
4. Email/password auth (P3) - Fallback option
5. Password reset (P3) - Required if email/password implemented
6. Microsoft OAuth (P3) - Additional OAuth provider
