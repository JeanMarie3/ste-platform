from datetime import datetime
import json
from typing import Any, Dict, List

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import ExecutionStatus, PlatformType, ReviewStatus


class TestStep(BaseModel):
    action: str
    target: str
    value: str | None = None


class AssertionRule(BaseModel):
    type: str
    value: str | None = None
    target: str | None = None


class TestCaseRead(BaseModel):
    id: str
    requirement_id: str
    title: str
    objective: str
    platform: PlatformType
    priority: str
    review_status: ReviewStatus
    steps: List[TestStep]
    assertions: List[AssertionRule]
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TestCaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    objective: str | None = Field(default=None, min_length=5)
    priority: str | None = None
    steps: List[TestStep] | None = None
    assertions: List[AssertionRule] | None = None
    tags: List[str] | None = None


class ReviewAction(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def parse_json_string_body(cls, data: Any) -> Any:
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return data

    review_status: str
    comment: str | None = None


class Verdict(BaseModel):
    status: ExecutionStatus
    reason: str
    confidence: float


class StepExecutionRead(BaseModel):
    step_number: int
    action: str
    expected_result: str
    actual_result: str
    verdict: Verdict
    evidence: List[str] = Field(default_factory=list)


class TestRunRead(BaseModel):
    id: str
    test_case_id: str
    agent_type: PlatformType
    environment: str = "local"
    run_mode: str = "headless"
    status: ExecutionStatus
    summary_reason: str
    confidence_score: float
    started_at: datetime
    finished_at: datetime | None = None
    steps: List[StepExecutionRead] = Field(default_factory=list)
