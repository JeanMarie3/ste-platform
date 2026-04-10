# Software Testing Engine (STE) Starter Project

This repository is a working starter implementation of a web-based Software Testing Engine (STE).

## Modules

- `backend/` - FastAPI control plane for requirements, generated test cases, reviews, and execution orchestration
- `agent/` - execution agent that simulates platform-specific runs and returns evidence-backed step verdicts
- `frontend/` - React + TypeScript web UI to create requirements, generate test cases, approve them, and start executions
- `docs/` - architecture notes and roadmap

## Open in IntelliJ

Open the root folder `ste-platform` in IntelliJ IDEA.

## Local run without Docker

If you want headed Playwright runs, start the stack locally instead of through Docker:

```powershell
cd C:\Users\Jean001\source\ste-platform
.\scripts\local-build-run.ps1
```

This compiles the backend, builds the frontend, installs local Playwright Chromium for the agent when needed, and starts the local services.

### Keep local and Docker data synchronized

To see the same requirements/test cases in local and Docker, both must use the same PostgreSQL DB.

1. Ensure root `.env` contains:

```dotenv
DATABASE_URL=postgresql+psycopg://ste_user:ste_password@localhost:5432/ste_platform
AGENT_BASE_URL=http://localhost:8010
```

2. Keep only postgres running in Docker when you run local services:

```powershell
cd C:\Users\Jean001\source\ste-platform
docker compose up -d postgres
```

`./scripts/dev-up.ps1` now auto-starts `postgres` when `DATABASE_URL` is PostgreSQL.

## What is implemented now

- SQL-backed persistence in the backend (SQLite by default, PostgreSQL-ready)
- requirement creation API
- generated test cases by platform
- review status updates
- backend-to-agent execution dispatch
- stored execution runs with step-level verdicts
- frontend workflow for create -> generate -> approve -> execute

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`.

### Database configuration (recommended: PostgreSQL)

For production, use PostgreSQL and set `DATABASE_URL` in your root `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://ste_user:ste_password@localhost:5432/ste_platform
```

If `DATABASE_URL` is not set, backend falls back to local SQLite at `backend/data/ste.db`.

To migrate existing SQLite data to your configured `DATABASE_URL`:

```powershell
cd C:\Users\Jean001\source\ste-platform\backend
python -m scripts.migrate_sqlite_to_database --sqlite-path .\data\ste.db
```

## Agent

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --reload --port 8010
```

Agent runs on `http://localhost:8010`.

For web test execution, the agent now runs real browser steps via Playwright.
You can choose headless or headed mode from the Dashboard before starting a web execution.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

### Standalone React DevTools (optional)

If you use `react-devtools` (the standalone app), enable the bridge in `frontend/.env.development`:

```dotenv
VITE_ENABLE_REACT_DEVTOOLS=true
```

Then restart Vite and run DevTools:

```powershell
cd C:\Users\Jean001\source\ste-platform\frontend
npm run dev
```

```powershell
react-devtools
```

Notes:
- this is injected only on `localhost` / `127.0.0.1`
- keep it disabled for shared/production environments

## OpenAI webhook setup

This project now exposes a backend webhook receiver at:

- local route: `http://127.0.0.1:8000/api/v1/openai/webhooks`

Important:
- OpenAI cannot call `http://127.0.0.1:5173/` or any other localhost URL from the internet.
- The webhook must point to the **backend**, not the Vite frontend.
- You must expose the backend with a public **HTTPS** URL such as ngrok or Cloudflare Tunnel.

Recommended flow:

1. Start the project.
2. Expose backend port `8000` with a tunnel.
3. Use this webhook URL in the OpenAI dashboard:
   - `https://your-public-host/api/v1/openai/webhooks`
4. Copy the webhook signing secret from OpenAI into repo root `.env` as `OPENAI_WEBHOOK_SECRET`.

Example `.env` values:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_WEBHOOK_SECRET=whsec_your_openai_webhook_secret_here
BACKEND_PUBLIC_BASE_URL=https://your-public-host
```

Example ngrok command:

```powershell
ngrok http 8000
```

Then create the webhook in OpenAI using:

- Name: `ste-test`
- URL: `https://your-public-host/api/v1/openai/webhooks`
- Event type: `response.completed`

You can test the local route yourself with:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/v1/openai/webhooks -Method Post
```

Without a valid OpenAI signature, the route should reject the request with `400 Invalid webhook signature`, which confirms the endpoint is live and protected.

## One-command startup on Windows (PowerShell)

From the repository root:

```powershell
cd C:\Users\Jean001\source\ste-platform
.\scripts\dev-up.ps1
```

This script will:
- create backend/agent virtual environments if missing
- install Python/npm dependencies when needed
- start backend, agent, and frontend
- wait for health endpoints before finishing

Health checks:
- Backend: `http://127.0.0.1:8000/api/v1/health`
- Agent: `http://127.0.0.1:8010/health`
- Frontend: `http://127.0.0.1:5173/`

Stop all services started by the script:

```powershell
cd C:\Users\Jean001\source\ste-platform
.\scripts\dev-stop.ps1
```

Useful options:
- skip installs: `./scripts/dev-up.ps1 -NoInstall`
- force reinstall deps: `./scripts/dev-up.ps1 -ForceReinstall`
- skip Playwright browser install: `./scripts/dev-up.ps1 -SkipBrowserInstall`

## Suggested next implementation steps

1. Replace synthetic agent adapters with real Playwright-based web execution
2. Add export to Excel and Word from the backend
3. Add authentication and role-based access control
4. Add artifact file storage instead of artifact URIs only
5. Add Alembic schema migrations and versioned rollout scripts
6. Add mobile and database deep adapters
