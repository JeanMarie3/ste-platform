import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.models.contracts import AgentExecutionRequest, AgentExecutionResponse
from app.services.execution_agent_service import ExecutionAgentService


logger = logging.getLogger(__name__)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("STE Agent starting up")
    yield
    logger.info("STE Agent shutting down")


app = FastAPI(title="STE Agent", version="0.1.0", lifespan=lifespan)
service = ExecutionAgentService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/execute", response_model=AgentExecutionResponse)
def execute(payload: AgentExecutionRequest) -> AgentExecutionResponse:
    return service.execute(payload)
