import json
from typing import Any

from openai import OpenAI

from app.core.config import settings


class AIService:
    def __init__(self) -> None:
        self.default_api_key = settings.openai_api_key
        self.client = OpenAI(api_key=self.default_api_key) if self.default_api_key else None
        self.model = "gpt-4o-mini"

    @property
    def available(self) -> bool:
        return self.client is not None

    def available_for(self, api_key: str | None = None) -> bool:
        key = (api_key or "").strip() or self.default_api_key
        return bool(key)

    def _client_for(self, api_key: str | None = None) -> OpenAI | None:
        key = (api_key or "").strip() or self.default_api_key
        if not key:
            return None
        return self.client if key == self.default_api_key and self.client is not None else OpenAI(api_key=key)

    def generate_test_case(
        self,
        requirement_title: str,
        requirement_description: str,
        business_rules: list[str],
        platform: str,
        target_url: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Generate AI-powered test steps and assertions for a requirement + platform."""
        client = self._client_for(api_key)
        if client is None:
            return {}

        rules_text = "\n".join(f"- {r}" for r in business_rules) if business_rules else "None"
        target_text = target_url or "Not provided"
        prompt = f"""You are a senior software QA engineer. Generate a detailed, realistic test case for the requirement below targeting the {platform} platform.

Requirement title: {requirement_title}
Requirement description: {requirement_description}
Business rules:
{rules_text}
Platform: {platform}
Target application URL: {target_text}

Return ONLY a JSON object with this exact structure:
{{
  "title": "concise test case title",
  "objective": "one-sentence testing objective",
  "steps": [
    {{"action": "verb", "target": "element or endpoint or table", "value": "input value or null"}},
    ...
  ],
  "assertions": [
    {{"type": "assertion_type", "target": "element or field or null", "value": "expected value or null"}},
    ...
  ]
}}

Platform guidance:
- web: actions like navigate, input, click, verify_element, take_screenshot; assertions like url_contains, element_visible, text_equals
- api: actions like authenticate, request, check_header; assertions like status_code, json_field_present, response_time_under
- database: actions like connect, query, execute_stored_proc; assertions like row_count_greater_than, field_equals, schema_valid

Generate 4-7 meaningful steps and 2-4 assertions specific to this requirement. Be concrete."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            result = json.loads(response.choices[0].message.content)
            if not isinstance(result.get("steps"), list) or not result["steps"]:
                return {}
            return result
        except Exception:
            return {}

    def suggest_requirement(self, description: str, api_key: str | None = None) -> dict[str, Any]:
        """Convert a plain-English description into a structured requirement."""
        client = self._client_for(api_key)
        if client is None:
            return {}

        prompt = f"""You are a software requirements analyst. Structure the following natural language description into a formal software requirement.

Description: {description}

Return ONLY a JSON object with this exact structure:
{{
  "title": "concise requirement title (5-10 words)",
  "description": "clear formal requirement description (1-3 sentences)",
  "platforms": ["web"],
  "priority": "medium",
  "risk": "medium",
  "business_rules": ["rule 1", "rule 2"]
}}

- platforms: array from [web, api, database, mobile, desktop] — infer from context
- priority: low | medium | high — infer from urgency/importance cues
- risk: low | medium | high — infer from business impact
- business_rules: specific constraints, validation rules, or acceptance criteria (2-5 items)
Be specific, actionable, and professional."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {}

