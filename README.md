# org-service

**Phase 1: Minimal Google OAuth + JWT Authentication (No Database)**

A lightweight FastAPI service that handles Google OAuth login and issues JWT tokens with hardcoded organizational values. Built for solo use until Phase 2 (multi-tenant database) is needed.

---

## 🎯 What This Does (Phase 1)

**ONLY TWO THINGS:**

1. **Google OAuth Login** - Authenticate users via Google
2. **JWT Generation** - Issue JWT tokens with hardcoded `org_id` and `is_owner=true`

**NO DATABASE. NO USER STORAGE. NO ORG STRUCTURE.**

All users get the same `org_id` in their JWT. Perfect for solo development across multiple services.

---

## ✅ Features

- 🔐 **Google OAuth Login**
  - Redirects to Google OAuth consent screen
  - Handles OAuth callback
  - Extracts user email and Google user ID

- 🔑 **JWT Token Issuance**
  - Generates JWT with:
    - `sub`: Google user ID
    - `org_id`: Hardcoded to `11111111-1111-1111-1111-111111111111`
    - `email`: User's email from Google
    - `is_owner`: Always `true` (everyone is owner in Phase 1)
    - `exp`: 7 days expiration

- 🔒 **JWT Validation Middleware**
  - Validates JWT signature and expiration
  - Attaches user context to `request.state.user`
  - Returns 401 for invalid/missing tokens

- 🏥 **Health Check**
  - `/health` endpoint for monitoring

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

**Required values:**

```env
# Get from https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Optional (defaults provided)
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=604800  # 7 days
HARDCODED_ORG_ID=11111111-1111-1111-1111-111111111111
```

### 3. Run the Service

```bash
uvicorn org_service.main:app --reload --port 8000
```

Service runs at: `http://localhost:8000`

**API Docs:** `http://localhost:8000/docs`

---

## 🔐 Google OAuth Setup

### Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create new project (or select existing)
3. Enable "Google+ API"
4. Create OAuth 2.0 Client ID:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/auth/callback`
5. Copy Client ID and Client Secret to `.env`

### Test Accounts

During development, you may need to add test users to your OAuth consent screen if it's not published.

---

## 📡 API Endpoints

### Public Endpoints (No JWT Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/login` | Redirects to Google OAuth |
| GET | `/auth/callback` | OAuth callback, returns JWT |

### Protected Endpoints (JWT Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/secure/whoami` | Returns user info from JWT |

---

## 🔑 Authentication Flow

### 1. Login

```bash
# User visits login endpoint
curl http://localhost:8000/auth/login
# → Redirects to Google OAuth
```

### 2. Google Callback

After user approves, Google redirects back to:

```
http://localhost:8000/auth/callback?code=...&state=...
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Access Protected Routes

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/secure/whoami
```

**Response:**

```json
{
  "user": {
    "google_sub": "1234567890",
    "org_id": "11111111-1111-1111-1111-111111111111",
    "email": "user@example.com",
    "is_owner": true
  }
}
```

---

## 🧪 Testing

### Install Test Dependencies

```bash
pip install -r dev-requirements.txt
```

### Run Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/routes/test_auth_routes.py -v

# With coverage
pytest --cov=org_service --cov-report=html
```

### Test Coverage

Current tests cover:
- ✅ Google OAuth redirect
- ✅ OAuth callback with valid/invalid state
- ✅ JWT generation with hardcoded values
- ✅ JWT middleware validation
- ✅ Protected route access control
- ✅ Expired token rejection

---

## 📁 Project Structure

```
org-service/
├── org_service/
│   ├── main.py                  # FastAPI app + health check
│   ├── config.py                # Settings (Google OAuth, JWT, hardcoded org_id)
│   ├── logging_config.py        # Logging setup
│   ├── routes/
│   │   ├── auth_routes.py       # /auth/login, /auth/callback
│   │   └── secure_routes.py     # /secure/whoami
│   ├── services/
│   │   └── auth_service.py      # Google OAuth handling, JWT generation
│   ├── middleware/
│   │   └── jwt_middleware.py    # JWT validation
│   └── utils/
│       └── jwt.py               # JWT encode/decode functions
├── tests/
│   ├── conftest.py              # Test fixtures
│   ├── routes/
│   │   ├── test_auth_routes.py
│   │   └── test_secure_routes.py
│   └── middleware/
│       └── test_jwt_middleware.py
├── .env.example                 # Environment template
├── requirements.txt             # Production dependencies
├── dev-requirements.txt         # Test dependencies
└── README.md                    # This file
```

---

## 🔄 What Happens in Phase 2?

When you onboard your first customer, you'll add:

1. **Database (PostgreSQL)**
   - Organizations table
   - Users table
   - User-org relationships

2. **Dynamic org_id**
   - Look up user's organization from database
   - Support multiple organizations

3. **Role Management**
   - Store roles in database
   - First user in org = owner
   - Subsequent users = member (or invited role)

4. **Invite System**
   - Allow users to join existing orgs

**But NOT NOW.** Phase 1 keeps it minimal.

---

## 🛠️ Development

### Code Formatting

```bash
# Format with black
black org_service/ tests/

# Lint with ruff
ruff check org_service/ tests/
```

### Type Checking

```bash
mypy org_service/
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

---

## 🐛 Troubleshooting

### OAuth "state mismatch" error

**Cause:** Session cookies not persisting between `/auth/login` and `/auth/callback`

**Solutions:**
- Use incognito window
- Clear cookies
- Ensure `SessionMiddleware` is configured (it is by default)

### JWT validation fails

**Cause:** `JWT_SECRET_KEY` mismatch between token creation and validation

**Solutions:**
- Verify `.env` has correct `JWT_SECRET_KEY`
- Regenerate tokens after changing secret
- Check `JWT_ALGORITHM` matches (should be HS256)

### Import errors after simplification

**Cause:** Old code may still reference deleted database models

**Solutions:**
- Search for imports of `org_service.models`, `org_service.db`
- These should no longer exist in Phase 1
- Check that tests don't reference database fixtures

---

## 📝 Notes

- **Security:** JWT_SECRET_KEY should be 256-bit random (use `openssl rand -hex 32`)
- **Expiry:** Default 7 days for Phase 1 (can adjust in `.env`)
- **CORS:** Not configured - add if needed for frontend
- **HTTPS:** Use reverse proxy (nginx, Caddy) in production
- **Logging:** Uses Python logging, outputs to console

---

## 🤝 Contributing

This is Phase 1 (minimal implementation). Contributions should:
- Maintain simplicity (no database)
- Add tests for new features
- Follow existing code style (black, ruff)
- Update this README

---

## 📄 License

MIT (or your preferred license)

---

## 🔗 Related Services

This auth service is designed to work with:
- **sync-hostaway** - Property sync service
- **sync-airbnb** - Airbnb integration
- **property-ui** - Frontend dashboard

All services validate JWTs issued by org-service.
