import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from urllib import error, request as urllib_request

from app.core.config import settings
from app.domain.enums import ExecutionStatus, PlatformType
from app.repositories.sql_store import TestCaseRepository, TestRunRepository
from app.schemas.common import new_id, utc_now
from app.schemas.executions import StartExecutionRequest
from app.schemas.testcases import StepExecutionRead, TestRunRead


class ExecutionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.test_case_repository = TestCaseRepository()
        self.test_run_repository = TestRunRepository()
        self._executor = ThreadPoolExecutor(max_workers=max(2, int(os.getenv("EXECUTION_MAX_PARALLEL", "4"))))

    def start_execution(self, request: StartExecutionRequest) -> TestRunRead:
        test_case = self.test_case_repository.get(request.test_case_id)
        if test_case is None:
            raise KeyError(request.test_case_id)

        started_at = utc_now()
        run_mode = "headless" if request.headless else "headed"

        run = TestRunRead(
            id=new_id("RUN"),
            test_case_id=test_case.id,
            agent_type=request.agent_type,
            environment=request.environment,
            run_mode=run_mode,
            status=ExecutionStatus.RUNNING,
            summary_reason="Execution started",
            confidence_score=0.0,
            started_at=started_at,
            finished_at=None,
            steps=[],
        )
        created_run = self.test_run_repository.create(run)
        self._executor.submit(self._complete_run, created_run, request, test_case)
        return created_run

    def _complete_run(self, run: TestRunRead, request: StartExecutionRequest, test_case) -> None:
        try:
            try:
                target_url = self._extract_target_url(test_case.metadata)
                if test_case.platform == PlatformType.WEB and not target_url:
                    response = self._local_blocked_response(
                        "This web test case has no target URL. Regenerate from a requirement with target_url."
                    )
                else:
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
            except Exception as exc:
                response = self._local_failed_response(f"Execution dispatch failed: {self._safe_error_text(exc)}")

            response_status = str(response.get("status") or ExecutionStatus.FAILED.value)
            response_message = str(response.get("message") or "Execution completed with no message")
            response_confidence = float(response.get("confidence") or 0.65)
            response_steps = response.get("steps") if isinstance(response.get("steps"), list) else []
            try:
                final_status = ExecutionStatus(response_status)
            except ValueError:
                final_status = ExecutionStatus.FAILED

            updated_run = run.model_copy(
                update={
                    "status": final_status,
                    "summary_reason": response_message,
                    "confidence_score": response_confidence,
                    "finished_at": utc_now(),
                    "steps": self._parse_response_steps(response_steps),
                }
            )
        except Exception as exc:
            self.logger.exception("Run %s failed during completion finalization", run.id)
            updated_run = run.model_copy(
                update={
                    "status": ExecutionStatus.FAILED,
                    "summary_reason": f"Execution finalization failed: {self._safe_error_text(exc)}",
                    "confidence_score": 0.5,
                    "finished_at": utc_now(),
                    "steps": self._parse_response_steps(self._local_failed_response(self._safe_error_text(exc)).get("steps") or []),
                }
            )

        try:
            if not self.test_run_repository.update_result(updated_run):
                self.logger.warning("Run %s could not be updated after execution completion", run.id)
        except Exception:
            self.logger.exception("Run %s update_result raised an exception", run.id)

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
            with urllib_request.urlopen(req, timeout=60) as response:
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

    def _local_blocked_response(self, reason: str) -> dict:
        return {
            "status": ExecutionStatus.BLOCKED.value,
            "message": reason,
            "confidence": 0.98,
            "steps": [
                {
                    "step_number": 1,
                    "action": "pre_execution_validation",
                    "expected_result": "Execution can be dispatched",
                    "actual_result": reason,
                    "verdict": {
                        "status": ExecutionStatus.BLOCKED.value,
                        "reason": reason,
                        "confidence": 0.98,
                    },
                    "evidence": [],
                }
            ],
        }

    def _local_failed_response(self, reason: str) -> dict:
        return {
            "status": ExecutionStatus.FAILED.value,
            "message": reason,
            "confidence": 0.65,
            "steps": [
                {
                    "step_number": 1,
                    "action": "dispatch_to_agent",
                    "expected_result": "Agent accepts and executes run",
                    "actual_result": reason,
                    "verdict": {
                        "status": ExecutionStatus.FAILED.value,
                        "reason": reason,
                        "confidence": 0.65,
                    },
                    "evidence": [],
                }
            ],
        }

    def _safe_error_text(self, exc: Exception) -> str:
        text = str(exc).strip()
        if text:
            return text
        return f"{exc.__class__.__name__} (no details)"

    def _parse_response_steps(self, response_steps: list) -> list[StepExecutionRead]:
        parsed_steps: list[StepExecutionRead] = []
        for step in response_steps:
            try:
                parsed_steps.append(StepExecutionRead.model_validate(step))
            except Exception as exc:
                self.logger.warning("Skipping malformed step payload from agent: %s", self._safe_error_text(exc))
        return parsed_steps

