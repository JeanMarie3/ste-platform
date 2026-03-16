from app.adapters.api import ApiAdapter
from app.adapters.database import DatabaseAdapter
from app.adapters.web import WebAdapter
from app.models.contracts import AgentExecutionRequest, AgentExecutionResponse


class ExecutionAgentService:
    def execute(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        adapter = self._resolve_adapter(request.platform)
        adapter.prepare()
        result = adapter.execute(request.model_dump())
        return AgentExecutionResponse(
            run_reference=f"agent-{request.test_case_id}",
            status=result["status"],
            message=result["message"],
            confidence=result["confidence"],
            steps=result["steps"],
        )

    def _resolve_adapter(self, platform: str):
        if platform == "web":
            return WebAdapter()
        if platform == "api":
            return ApiAdapter()
        if platform == "database":
            return DatabaseAdapter()
        return WebAdapter()
