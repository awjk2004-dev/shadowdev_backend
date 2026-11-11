# ShadowDev Backend

ShadowDev Backend is a REST API for the ShadowDev Flutter application. It is
built with FastAPI, SQLAlchemy, PostgreSQL, and JWT bearer authentication.

## Features

- User registration and bearer-token login
- User-scoped tasks, player progress, skills, weight tracking, and statistics
- PostgreSQL schema migrations managed with Alembic
- Password hashing with bcrypt
- Configurable API request limits and temporary login lockouts

## Requirements

- Python 3.12 recommended
- PostgreSQL database

## Run locally

1. Create and activate a virtual environment:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a local environment file from the example:

   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and set `DATABASE_URL` to your PostgreSQL connection string.
   Generate a unique `SECRET_KEY` (at least 32 characters), for example:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

   Do not commit `.env` or share its secret values.

5. Apply database migrations:

   ```bash
   alembic upgrade head
   ```

6. Start the development server:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API is available at `http://localhost:8000`. In development, interactive
API documentation is available at `http://localhost:8000/docs`.

## API overview

All versioned endpoints use the `/api/v1` prefix.

| Area | Endpoints |
| --- | --- |
| Health | `GET /`, `GET /health`, `GET /api/v1/ping` |
| Authentication | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` |
| Current user | `GET /api/v1/auth/me`, `PUT /api/v1/auth/me` |
| Tasks | `/api/v1/tasks` |
| Player | `/api/v1/player` |
| Skills | `GET /api/v1/skills/me`, `POST /api/v1/skills/me/{skill_id}/unlock`, `POST /api/v1/skills/me/reset` |
| Weight | `/api/v1/weight` |
| Statistics | `/api/v1/stats` |

Most application endpoints require an `Authorization: Bearer YOUR_ACCESS_TOKEN`
header. Login accepts form-encoded `username` and `password` fields and returns
a bearer token. Registration currently requires a password with at least 12
characters, including uppercase and lowercase letters, a number, and a symbol.

User data is scoped to the authenticated user. The API does not currently define
administrator roles or an admin interface.

### Skill tree and skill points

The skill-tree migration seeds the canonical tree and adds persistent unlock
state and player skill points. Players start with 10 SP; each newly reached
level grants one additional SP. Unlock requests validate prerequisites and
costs on the server. Resetting the tree locks all its skills and restores the
player's full earned SP balance (`10 + level - 1`). Existing players are
backfilled from their current XP-derived level.

The mobile app uses `GET /api/v1/skills/me` to load the tree and
`POST /api/v1/skills/me/{skill_id}/unlock` to unlock a skill. The legacy
`PATCH /api/v1/skills/me/{skill_id}` status-progression endpoint remains
available. Run `alembic upgrade head` before deploying the client changes.

## Configuration

Configuration is loaded from environment variables, or from `.env` for local
development.

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection URL. The application normalizes common PostgreSQL URL schemes to the `psycopg` driver. |
| `SECRET_KEY` | Unique secret used to sign access tokens; at least 32 characters. |
| `ENVIRONMENT` | `development`, `staging`, or `production`. |
| `DEBUG` | Enables SQLAlchemy query logging when true. Keep false in production. |
| `ALGORITHM` | JWT signing algorithm; defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime; defaults to 43200 minutes. |
| `API_RATE_LIMIT_REQUESTS` | Maximum API requests per IP in the configured time window; defaults to 120. |
| `API_RATE_LIMIT_WINDOW_SECONDS` | API request-limit window in seconds; defaults to 60. |
| `LOGIN_FAILURE_LIMIT` | Failed login attempts before a temporary lockout; defaults to 5. |
| `LOGIN_LOCKOUT_SECONDS` | Login lockout window in seconds; defaults to 900. |
| `CORS_ORIGINS` | JSON array of allowed browser origins. For a Flutter native app only, use `[]`. |

When `ENVIRONMENT=production`, the application rejects `DEBUG=true`, placeholder
secrets, and non-HTTPS CORS origins. HTTPS/TLS must be enabled at the hosting
platform or reverse proxy.

## Deploy to Render

Create a Render **Web Service** connected to this repository and configure:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`

Set these environment variables in the Render dashboard:

```text
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=<your PostgreSQL connection URL>
SECRET_KEY=<a unique secret generated for this deployment>
CORS_ORIGINS=[]
```

Also set any rate-limit or token settings you want to override. Never put
production secrets in this README, the repository, or a committed `.env` file.

Render's free web services can sleep after inactivity, so the first request
after a sleep may take longer. Their local filesystem is ephemeral; do not use
it for persistent data or SQLite. Use PostgreSQL for application data. The
in-memory request limiter and login lockout are reset when the service restarts
and are not shared across multiple service instances. This setup is intended for
testing or small personal projects, not production workloads that need
consistent abuse protection or high availability.

## Tests

Run the focused security-control tests with:

```bash
python -m unittest tests.test_security_controls
```
         