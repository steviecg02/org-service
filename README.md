# org-service

A FastAPI-based authentication and organizational identity service. Supports Google OAuth login, role-aware JWT issuance, and secure route protection via middleware.

---

## ✅ Features

- 🔐 **Google OAuth Login**
  - Uses Authlib to redirect and authenticate via Google
  - Receives `id_token`, extracts user info, and handles callback

- 🪪 **Account & User Creation**
  - On first login, creates a new `account` and `user` tied to the Google identity
  - Returns JWT with `account_id`, `user_id`, `email`, and `roles`

- 🔑 **JWT Authentication**
  - Access tokens are signed and validated via middleware
  - Role-based access control available (via `roles` claim)

- 🔒 **Secure Routes**
  - Example: `/secure/whoami` returns current user info if authenticated

---

## 🧪 Development

### Run Locally

```bash
make venv
```

App runs at `http://localhost:8000`

### Environment

Populate your `.env` file:

```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
JWT_SECRET=super-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/org_service
```

> ✅ `JWT_SECRET` must be long and random
> ✅ The test database will use `org_service_test` automatically (no `.env.test` needed)

---

### Alembic Migrations

Use Alembic to manage schema:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

> ✅ Tables are now created only via Alembic — not from `Base.metadata.create_all()`

---

### Linting & Formatting

```bash
make lint   # Runs ruff
make fmt    # Runs black
```

> Set up a `.pre-commit-config.yaml` if you want this enforced automatically before commits.

---

## 🧪 Testing

### Run Tests

```bash
make test
```

- Uses `_test` suffix on the default DB name (`org_service_test`)
- Automatically creates the test DB if not present
- Applies Alembic migrations before each test session

### Notes

- ✅ `get_test_session()` now returns a context-managed session for async tests
- ✅ `Base.metadata.drop_all()` is no longer used — replaced by real migrations
- ✅ Test DB logic avoids `.env.test` complexity

---

## 🧠 Known Dev Quirks

- **First Google login may fail** in dev with `state mismatch` error
  > This happens when the user is already logged in with Google. Clear cookies or use a new incognito window if needed.

---

## 🧩 Folder Structure

```
org_service/
├── main.py                  # FastAPI app entrypoint
├── routes/
│   └── auth_routes.py       # OAuth endpoints
├── services/
│   └── auth_service.py      # Google OAuth, token handling, user/account logic
├── middleware/
│   └── jwt_middleware.py    # JWT validation
├── models/
│   ├── user.py              # User table
│   └── account.py           # Account table
├── config.py                # Settings via Pydantic
├── db.py                    # DB engine + Alembic integration
├── alembic/                 # Migrations
tests/
└── utils/
    └── test_db.py           # Async engine + test DB session helper
```

---

## 📝 TODO

### 🧠 Role & Account Logic

- [ ] Replace default role `["owner"]` with `"admin"` (or `"account_admin"`)
- [ ] Make role assignment **account-scoped**, not global
- [ ] When user logs in:
  - [ ] Extract domain from email
  - [ ] Check if an `account` exists for domain
  - [ ] If not, create new account and set user role = `"admin"`
  - [ ] If yes, add user to existing account, with default role = `"member"`

### 🔐 Future Authentication Features

- [ ] Add support for Microsoft OAuth
- [ ] Add email/password login (non-OAuth fallback)
- [ ] Add refresh tokens
- [ ] Add invite-based account joining
- [ ] Protect admin-only routes via role check

---

## 🔍 Notes

- ✅ All auth logic separated from routes into `services/`
- ✅ All table creation moved to Alembic
- ✅ Full test coverage of JWT middleware and login flows
- This service is production-hardened but still scoped to a single-tenant org setup. Multi-tenant support will follow.
