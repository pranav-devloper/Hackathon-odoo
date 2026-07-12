# Hackathon Auth API (FastAPI)

A complete authentication backend with email verification, JWT access/refresh
tokens, OTP-based password reset, and role-based authorization.

## Stack
- **FastAPI** + Uvicorn
- **SQLAlchemy 2.0** (SQLite, `create_all` on startup)
- **PyJWT** for access & refresh tokens
- **bcrypt** for password hashing
- **Console email** (OTP + verification link printed to the server log)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Built frontend: http://localhost:8000/  (after `npm run build` in `frontend/`)

## Frontend (React SPA)

The `frontend/` folder is a Vite + React app with client-side routing
(`react-router-dom`) that drives the `/auth/*` backend.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /auth -> http://localhost:8000)
# production build:
npm run build      # outputs to frontend/dist, served by FastAPI at http://localhost:8000/
```

Routes: `/signup`, `/verify`, `/login`, `/forgot-password`, `/reset-password`,
`/profile` (protected), `/admin` (admin role). Tokens are stored in
`localStorage` and sent as `Bearer` headers.

## Configuration
Copy `.env.example` to `.env` (optional — sensible defaults are built in):

| Var | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | `sqlite:///./app.db` | DB connection |
| `SECRET_KEY` | dev value | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `OTP_EXPIRE_MINUTES` | `10` | OTP lifetime |
| `FRONTEND_URL` | `http://localhost:8000` | Base URL for verification links |

## Auth flow
1. `POST /auth/signup` → creates a user (role `user`), prints an OTP to console.
2. `POST /auth/verify-email` → verify with the OTP.
3. `POST /auth/login` → returns `access_token` + `refresh_token`.
4. `GET /auth/me` → protected; send `Authorization: Bearer <access_token>`.
5. `POST /auth/refresh` → rotate tokens using the refresh token.
6. `POST /auth/logout` → revoke the refresh token.
7. `POST /auth/forgot-password` → prints a reset OTP.
8. `POST /auth/reset-password` → set a new password with the OTP.

## Role-based authorization
Roles are seeded on startup: `user` and `admin`. Use the dependency factories
in `app/dependencies/roles.py`:

```python
from app.dependencies.roles import require_role, require_roles

@router.get("/admin/me")
def admin_me(user = Depends(require_role("admin"))): ...
```

## Endpoints
See `postman/Hackathon-Auth.postman_collection.json` (import into Postman) or
the table above. A quick curl test:

```bash
curl -X POST localhost:8000/auth/signup -H 'Content-Type: application/json' \
  -d '{"email":"a@b.com","full_name":"A","password":"secret123"}'
```
