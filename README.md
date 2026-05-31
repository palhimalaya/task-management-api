# Task Management API

A REST API for task management with **JWT authentication**, **Role-Based Access Control (RBAC)**, and a clean **policy-based authorization layer** — built with FastAPI, PostgreSQL, and async SQLAlchemy.

---

## Quick Start (Recommended: Docker)

```bash
docker-compose up --build
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Default Dev Accounts

On startup, optional seed users are created from the credentials in the environment. Docker Compose includes one account for each role so you can quickly test RBAC flows:

| Role    | Email                 | Password      |
| ------- | --------------------- | ------------- |
| ADMIN   | `admin@example.com`   | `changeme123` |
| MANAGER | `manager@example.com` | `changeme123` |
| USER    | `user@example.com`    | `changeme123` |

Use these to log in via `/api/v1/auth/login` and get a JWT for testing role-scoped endpoints.

> **⚠️ Production:** Remove the seed email/password variables from your environment (or leave them blank). Seeds are skipped when these vars are unset — no hardcoded credentials are created.

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
| `MANAGER_EMAIL`               | Seed manager email — **dev only, leave blank in prod**  |
| `MANAGER_PASSWORD`            | Seed manager password — **dev only, leave blank in prod** |
| `USER_EMAIL`                  | Seed user email — **dev only, leave blank in prod**     |
| `USER_PASSWORD`               | Seed user password — **dev only, leave blank in prod**  |

---

## Running Tests

Tests use an in-memory SQLite database — no PostgreSQL required.

```bash
# Run all tests
pytest tests/ -v
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

### API Usage Flow

1. Start the stack with `docker-compose up --build`.
2. Open Swagger UI at `http://localhost:8000/docs`, or import the Postman collection from `docs/task-management-api.postman_collection.json`.
3. Log in with one of the seeded dev accounts:

```json
{
  "email": "admin@example.com",
  "password": "changeme123"
}
```

4. Copy `data.access_token` from the response and send it as a bearer token for protected endpoints.
5. Create a task as ADMIN or MANAGER:

```json
{
  "title": "Prepare project demo",
  "description": "Create a short walkthrough for the submission",
  "assigned_to": 3
}
```

6. Test role-specific behavior by logging in as `manager@example.com` or `user@example.com`.

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

## Database Structure

Database changes are managed with Alembic migrations in `alembic/versions/`.

Current schema:

```text
roles
├── id          integer primary key
└── name        varchar(50), unique, not null

users
├── id            integer primary key
├── full_name     varchar(100), nullable
├── email         varchar(100), unique, indexed, not null
├── password_hash varchar(255), not null
├── is_active     boolean, not null
└── role_id       integer, foreign key -> roles.id

tasks
├── id          integer primary key
├── title       varchar(100), not null
├── description text, nullable
├── status      enum(PENDING, IN_PROGRESS, COMPLETED), not null
├── due_date    timestamptz, nullable
├── created_at  timestamptz, not null, default now()
├── updated_at  timestamptz, not null, default now()
├── created_by  integer, foreign key -> users.id, nullable
└── assigned_to integer, foreign key -> users.id, nullable
```

Relationships:

- One role has many users.
- One user can create many tasks through `tasks.created_by`.
- One user can be assigned many tasks through `tasks.assigned_to`.
- Tasks may be unassigned.

Migration files:

- `330d3a9f866f_create_initial_schema.py`
- `d9c36a93b71b_add_full_name_to_user.py`

---

## API Testing Collection

A Postman collection is included at:

```text
docs/task-management-api.postman_collection.json
```

Import it into Postman, run one of the login requests, and the collection stores `access_token` automatically for protected requests. The collection also includes variables for `base_url`, `task_id`, and `user_id`.

Swagger is also available while the app is running:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Assumptions & Limitations

- Seeded dev accounts are for local testing only and should be disabled in production by leaving seed env vars blank.
- Public registration always creates a `USER`; manager/admin accounts are created through seed configuration for this assignment.
- The API uses JWT bearer authentication but does not implement refresh tokens.
- Task deletion is a hard delete.
- Status transitions only block moving `COMPLETED` tasks back to `PENDING` or `IN_PROGRESS`.
- CORS is open for development.
- Unit tests cover services and policies; full integration tests against PostgreSQL are not included.

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
├── docs/                      # API testing collection
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
