from fastapi import FastAPI

from app.models.contracts import AgentExecutionRequest, AgentExecutionResponse
from app.services.execution_agent_service import ExecutionAgentService

app = FastAPI(title="STE Agent", version="0.1.0")
service = ExecutionAgentService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/execute", response_model=AgentExecutionResponse)
def execute(payload: AgentExecutionRequest) -> AgentExecutionResponse:
    return service.execute(payload)
