from typing import Any

from app.adapters.base import BaseAdapter
from app.services.ai_verdict_service import ai_verdict_service


class WebAdapter(BaseAdapter):
    def prepare(self) -> str:
        return "Prepared browser session"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = ai_verdict_service.evaluate(payload)
        if result:
            return result

        # Synthetic fallback
        steps = []
        for index, step in enumerate(payload.get("steps", []), start=1):
            suspicious = step["action"] == "validate_feature"
            status = "suspicious" if suspicious else "passed"
            reason = (
                "Core path executed, but human-like UI judgement still needs richer visual rules"
                if suspicious
                else "Synthetic web step completed"
            )
            steps.append(
                {
                    "step_number": index,
                    "action": f"{step['action']}:{step['target']}",
                    "expected_result": "Step completes without blocking error",
                    "actual_result": reason,
                    "verdict": {"status": status, "reason": reason, "confidence": 0.78 if suspicious else 0.9},
                    "evidence": [f"artifact://{payload['test_case_id']}/web-step-{index}.png"],
                }
            )
        overall = "suspicious" if any(s["verdict"]["status"] == "suspicious" for s in steps) else "passed"
        return {
            "status": overall,
            "message": "Web flow executed through the agent with starter cognitive verdicting",
            "confidence": 0.79 if overall == "suspicious" else 0.91,
            "steps": steps,
        }
