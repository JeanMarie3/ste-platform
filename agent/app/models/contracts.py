from typing import Any

from pydantic import BaseModel, Field


class AgentExecutionRequest(BaseModel):
    test_case_id: str
    platform: str
    environment: str = "local"
    headless: bool = True
    target_url: str | None = None
    title: str = ""
    steps: list[dict[str, Any]] = Field(default_factory=list)
    assertions: list[dict[str, Any]] = Field(default_factory=list)


class AgentExecutionResponse(BaseModel):
    run_reference: str
    status: str
    message: str
    confidence: float
    steps: list[dict[str, Any]] = Field(default_factory=list)
