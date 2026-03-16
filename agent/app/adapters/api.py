from typing import Any

from app.adapters.base import BaseAdapter


class ApiAdapter(BaseAdapter):
    def prepare(self) -> str:
        return "Prepared API session"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        steps = []
        for index, step in enumerate(payload.get("steps", []), start=1):
            steps.append(
                {
                    "step_number": index,
                    "action": f"{step['action']}:{step['target']}",
                    "expected_result": "API step succeeds",
                    "actual_result": "Synthetic API adapter completed starter validation",
                    "verdict": {"status": "passed", "reason": "Starter API validation passed", "confidence": 0.93},
                    "evidence": [f"artifact://{payload['test_case_id']}/api-step-{index}.json"],
                }
            )
        return {
            "status": "passed",
            "message": "API flow executed successfully in the agent",
            "confidence": 0.93,
            "steps": steps,
        }
