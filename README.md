# Software Testing Engine (STE) Starter Project

This repository is a working starter implementation of a web-based Software Testing Engine (STE).

## Modules

- `backend/` - FastAPI control plane for requirements, generated test cases, reviews, and execution orchestration
- `agent/` - execution agent that simulates platform-specific runs and returns evidence-backed step verdicts
- `frontend/` - React + TypeScript web UI to create requirements, generate test cases, approve them, and start executions
- `docs/` - architecture notes and roadmap

## Open in IntelliJ

Open the root folder `ste-platform` in IntelliJ IDEA.

## What is implemented now

- SQLite-backed persistence in the backend
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

## Agent

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

Agent runs on `http://localhost:8010`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

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

## Suggested next implementation steps

1. Replace synthetic agent adapters with real Playwright-based web execution
2. Add export to Excel and Word from the backend
3. Add authentication and role-based access control
4. Add artifact file storage instead of artifact URIs only
5. Add PostgreSQL migration path for team deployment
6. Add mobile and database deep adapters
