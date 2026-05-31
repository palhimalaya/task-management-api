# Task Management API

A REST API for task management with **JWT authentication**, **Role-Based Access Control (RBAC)**, and a clean **policy-based authorization layer** — built with FastAPI, PostgreSQL, and async SQLAlchemy.

---

## Quick Start (Recommended: Docker)

```bash
docker-compose up --build
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Default Admin Account (dev only)

On first startup, a seeded **ADMIN** user is automatically created using the credentials from `.env`:

| Field    | Value               |
| -------- | ------------------- |
| Email    | `admin@example.com` |
| Password | `changeme123`       |

Use these to log in via `/api/v1/auth/login` and get a JWT for testing admin-only endpoints.

> **⚠️ Production:** Remove `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your environment (or leave them blank). The seed is skipped when these vars are unset — no hardcoded credentials are created.

---

## Local Setup

**Prerequisites:** Python 3.12+, PostgreSQL 14+

```bash
# 1. Clone & enter
git clone <repo-url>
cd task-management-api

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp env.example .env
# Edit .env — set DATABASE_URL and SECRET_KEY

# 5. Run migrations
alembic upgrade head

# 6. Start server
uvicorn app.main:app --reload
```

**`.env` key variables:**

| Variable                      | Description                                             |
| ----------------------------- | ------------------------------------------------------- |
| `DATABASE_URL`                | `postgresql+asyncpg://USER:PASS@HOST:PORT/DB`           |
| `SECRET_KEY`                  | JWT signing secret (min 32 chars)                       |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default: `30`)                               |
| `ADMIN_EMAIL`                 | Seed admin email — **dev only, leave blank in prod**    |
| `ADMIN_PASSWORD`              | Seed admin password — **dev only, leave blank in prod** |

---

## Running Tests

Tests use an in-memory SQLite database — no PostgreSQL required.

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## API Overview

**Base URL:** `http://localhost:8000/api/v1`

All protected endpoints require: `Authorization: Bearer <token>`

| Method | Endpoint             | Description              | Role           |
| ------ | -------------------- | ------------------------ | -------------- |
| POST   | `/auth/register`     | Register a user          | Public         |
| POST   | `/auth/login`        | Login, receive JWT       | Public         |
| GET    | `/users`             | List all users           | ADMIN          |
| POST   | `/tasks`             | Create a task            | ADMIN, MANAGER |
| GET    | `/tasks`             | List tasks (role-scoped) | All            |
| GET    | `/tasks/{id}`        | Get task                 | All (scoped)   |
| PATCH  | `/tasks/{id}`        | Update task              | Role-scoped    |
| DELETE | `/tasks/{id}`        | Delete task              | ADMIN          |
| PATCH  | `/tasks/{id}/assign` | Assign task              | ADMIN, MANAGER |

---

## RBAC & Permission Policy

Authorization is handled by a dedicated **policy layer** (`app/policies/`) — inspired by the Pundit pattern (Rails). Each operation delegates to `TaskPolicy` instead of embedding auth logic inside services.

```
TaskPolicy(user, task)
  .can_read()       # raises ForbiddenError if denied
  .can_update(payload)
  .can_assign()
```

| Action                  | ADMIN | MANAGER             | USER                   |
| ----------------------- | ----- | ------------------- | ---------------------- |
| View all tasks          | ✅    | ❌                  | ❌                     |
| View own/assigned tasks | ✅    | ✅                  | ✅                     |
| Create task             | ✅    | ✅                  | ❌                     |
| Update any task         | ✅    | ✅ (own/assigned)   | Status only (assigned) |
| Assign task             | ✅    | ✅ (own tasks only) | ❌                     |
| Delete task             | ✅    | ❌                  | ❌                     |

**Status workflow:** `PENDING → IN_PROGRESS → COMPLETED` (no backwards transitions)

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps/          # FastAPI auth and role-guard dependencies
│   │       ├── routes/        # HTTP routes for auth, users, and tasks
│   │       └── router.py      # API v1 route registration
│   ├── core/                  # Config, security helpers, custom exceptions
│   ├── db/                    # SQLAlchemy base, async session, seed data
│   ├── models/                # SQLAlchemy ORM models
│   ├── policies/              # Authorization policies such as TaskPolicy
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Business logic and database operations
│   ├── utils/                 # Shared enums and response helpers
│   └── main.py                # FastAPI application entrypoint
├── alembic/
│   ├── versions/              # Database migration revisions
│   ├── env.py                 # Alembic migration environment
│   └── script.py.mako         # Migration file template
├── tests/
│   ├── conftest.py            # Shared pytest fixtures
│   └── unit/
│       ├── policies/          # Policy-layer unit tests
│       └── services/          # Service-layer unit tests
├── docker-compose.yml         # Local API + PostgreSQL stack
├── Dockerfile                 # API container image
├── alembic.ini                # Alembic configuration
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
└── README.md
```

## Architecture

**Key design decisions:**

- **Policy layer**: Authorization lives in `app/policies/`, not inside services — keeps services focused on business logic
- **Async throughout**: `asyncpg` + `AsyncSession` for non-blocking I/O
- **Custom exceptions**: `ForbiddenError`, `NotFoundError` keep the service layer HTTP-free
- **Dependency injection**: `get_current_user` and `require_roles()` are composable FastAPI deps
- **`expire_on_commit=False`**: Prevents lazy-load errors in async context
