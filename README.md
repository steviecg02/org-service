
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
make dev
```

App runs at `http://localhost:8000`

### Environment

Make sure `.env` is populated with:

```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
JWT_SECRET=super-secret-key
```

> Use a strong random `JWT_SECRET`.

---

## 🧪 API

### `GET /auth/login`

- Redirects to Google for authentication.

### `GET /auth/callback`

- Handles the Google OAuth callback.
- Creates user and account if not found.
- Issues a JWT.

### `GET /secure/whoami`

- Returns current user info (requires valid JWT in `Authorization: Bearer <token>` header)

---

## 📦 JWT Payload Structure

Example token payload:

```json
{
  "sub": "user_id",
  "account_id": "account_id",
  "email": "user@example.com",
  "roles": ["admin"],
  "exp": 1752370179
}
```

---

## 🧩 Folder Structure

```
org_service/
├── main.py                 # FastAPI app with routes and middleware
├── routes/
│   └── auth_routes.py      # OAuth endpoints
├── services/
│   └── auth_service.py     # Handles token exchange, user/account creation
├── middleware/
│   └── jwt_middleware.py   # Validates JWT from requests
├── models/
│   └── user.py             # SQLAlchemy models (user, account, etc.)
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

- For now, any user can log in if Google authenticates them.
- This setup is meant for development; production hardening not yet complete.
