from datetime import datetime
from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import PlatformType


class RequirementCreate(BaseModel):
    project_code: str = Field(..., min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    platforms: List[PlatformType]
    priority: str = "medium"
    risk: str = "medium"
    business_rules: List[str] = Field(default_factory=list)
    target_url: str | None = None

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("target_url must be a valid http/https URL")
        return normalized


class RequirementRead(RequirementCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime


class RequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    description: str | None = Field(default=None, min_length=10)
    platforms: List[PlatformType] | None = None
    priority: str | None = None
    risk: str | None = None
    business_rules: List[str] | None = None
    target_url: str | None = None

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("target_url must be a valid http/https URL")
        return normalized

