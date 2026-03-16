from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.domain.enums import PlatformType


class RequirementCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    platforms: List[PlatformType]
    priority: str = "medium"
    risk: str = "medium"
    business_rules: List[str] = Field(default_factory=list)


class RequirementRead(RequirementCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
