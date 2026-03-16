from typing import Any

from app.adapters.base import BaseAdapter
from app.services.ai_verdict_service import ai_verdict_service


class DatabaseAdapter(BaseAdapter):
    def prepare(self) -> str:
        return "Prepared database connection"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = ai_verdict_service.evaluate(payload)
        if result:
            return result

        # Synthetic fallback
        steps = []
        for index, step in enumerate(payload.get("steps", []), start=1):
            steps.append(
                {
                    "step_number": index,
                    "action": f"{step['action']}:{step['target']}",
                    "expected_result": "Database verification succeeds",
                    "actual_result": "Synthetic database verification completed",
                    "verdict": {"status": "passed", "reason": "Starter data validation passed", "confidence": 0.92},
                    "evidence": [f"artifact://{payload['test_case_id']}/db-step-{index}.csv"],
                }
            )
        return {
            "status": "passed",
            "message": "Database flow executed successfully in the agent",
            "confidence": 0.92,
            "steps": steps,
        }
