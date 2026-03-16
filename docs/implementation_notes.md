# Implementation Notes

## Current choices

- FastAPI is the backend control plane for quick API delivery and AI-service friendliness.
- Execution is separated into an agent service so local or private-network runs can be added later.
- Persistence is in-memory for now to keep the starter runnable with minimal setup.
- The frontend is intentionally small and readable so it can be replaced or expanded quickly.

## Suggested next code tasks

1. Replace in-memory repositories with PostgreSQL and SQLAlchemy.
2. Add a job queue between backend and agent.
3. Implement Playwright in the web adapter.
4. Add evidence upload endpoints and object storage integration.
5. Add review comments and approval audit log tables.
6. Build forms in the frontend for requirement creation and test generation.
