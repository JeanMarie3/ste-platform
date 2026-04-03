import json
from urllib import error, request as urllib_request

from app.core.config import settings
from app.domain.enums import ExecutionStatus, PlatformType
from app.repositories.sql_store import TestCaseRepository, TestRunRepository
from app.schemas.common import new_id, utc_now
from app.schemas.executions import StartExecutionRequest
from app.schemas.testcases import StepExecutionRead, TestRunRead, Verdict


class ExecutionService:
    def __init__(self) -> None:
        self.test_case_repository = TestCaseRepository()
        self.test_run_repository = TestRunRepository()

    def start_execution(self, request: StartExecutionRequest) -> TestRunRead:
        test_case = self.test_case_repository.get(request.test_case_id)
        if test_case is None:
            raise KeyError(request.test_case_id)

        target_url = self._extract_target_url(test_case.metadata)
        if test_case.platform == PlatformType.WEB and not target_url:
            raise ValueError("This web test case has no target URL. Regenerate from a requirement with target_url.")

        started_at = utc_now()
        agent_payload = {
            "test_case_id": test_case.id,
            "platform": test_case.platform.value,
            "environment": request.environment,
            "headless": request.headless,
            "target_url": target_url,
            "steps": [step.model_dump() for step in test_case.steps],
            "assertions": [rule.model_dump() for rule in test_case.assertions],
            "title": test_case.title,
        }
        response = self._call_agent(agent_payload)
        run = TestRunRead(
            id=new_id("RUN"),
            test_case_id=test_case.id,
            agent_type=request.agent_type,
            environment=request.environment,
            status=response["status"],
            summary_reason=response["message"],
            confidence_score=response["confidence"],
            started_at=started_at,
            finished_at=utc_now(),
            steps=[StepExecutionRead.model_validate(step) for step in response["steps"]],
        )
        return self.test_run_repository.create(run)

    def _extract_target_url(self, metadata: dict | None) -> str | None:
        if not isinstance(metadata, dict):
            return None
        value = metadata.get("target_url")
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def list_runs(self) -> list[TestRunRead]:
        return self.test_run_repository.list()

    def get_run(self, run_id: str) -> TestRunRead | None:
        return self.test_run_repository.get(run_id)

    def delete_run(self, run_id: str) -> bool:
        return self.test_run_repository.delete(run_id)

    def _call_agent(self, payload: dict) -> dict:
        req = urllib_request.Request(
            url=f"{settings.agent_base_url}/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(req, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.URLError:
            return {
                "status": ExecutionStatus.BLOCKED.value,
                "message": "Execution agent is unavailable. Start the agent on port 8010 and retry.",
                "confidence": 0.98,
                "steps": [
                    {
                        "step_number": 1,
                        "action": "dispatch_to_agent",
                        "expected_result": "Agent accepts the run",
                        "actual_result": "Agent endpoint could not be reached",
                        "verdict": {
                            "status": ExecutionStatus.BLOCKED.value,
                            "reason": "Agent offline or unreachable",
                            "confidence": 0.98,
                        },
                        "evidence": [],
                    }
                ],
            }
