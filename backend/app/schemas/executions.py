from pydantic import BaseModel

from app.domain.enums import PlatformType


class StartExecutionRequest(BaseModel):
    test_case_id: str
    environment: str = "local"
    agent_type: PlatformType
