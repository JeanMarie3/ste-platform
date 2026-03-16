import json
from typing import Any

from openai import OpenAI

from app.core.config import settings


class AIVerdictService:
    """Uses GPT to simulate realistic test step execution and generate evidence-backed verdicts."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = "gpt-4o-mini"

    @property
    def available(self) -> bool:
        return self.client is not None

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Evaluate a full test case and return step verdicts + overall status, or None if unavailable."""
        if not self.available:
            return None

        test_case_id = payload.get("test_case_id", "unknown")
        platform = payload.get("platform", "web")
        title = payload.get("title", "Test Case")
        steps = payload.get("steps", [])
        assertions = payload.get("assertions", [])
        ext = {"web": "png", "api": "json", "database": "csv"}.get(platform, "log")

        prompt = f"""You are an automated software test execution engine. Simulate realistic execution of the following test case and return verdicts for each step.

Test case: {title}
Platform: {platform}
Environment: {payload.get("environment", "local")}

Steps:
{json.dumps(steps, indent=2)}

Assertions:
{json.dumps(assertions, indent=2)}

Return ONLY a JSON object with this exact structure:
{{
  "status": "passed",
  "message": "Concise 1-2 sentence execution summary",
  "confidence": 0.92,
  "steps": [
    {{
      "step_number": 1,
      "action": "action:target",
      "expected_result": "what should happen",
      "actual_result": "what happened during simulation (be specific to the action)",
      "verdict": {{
        "status": "passed",
        "reason": "why this step passed or failed",
        "confidence": 0.95
      }},
      "evidence": ["artifact://{test_case_id}/step-1.{ext}"]
    }}
  ]
}}

Rules:
- Include one entry per input step (total: {len(steps)} steps)
- status values: passed | failed | suspicious | inconclusive
- In a healthy system most steps pass; mark ambiguous UI/data checks as suspicious
- Make actual_result and reason specific to the platform action and target
- Adjust overall status: passed if all pass, suspicious if any suspicious, failed if any fail"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.6,
            )
            result = json.loads(response.choices[0].message.content)
            if not isinstance(result.get("steps"), list) or not result.get("status"):
                return None
            return result
        except Exception:
            return None


# Shared singleton — adapters import this
ai_verdict_service = AIVerdictService()

