from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])
_service = AIService()


class SuggestRequirementRequest(BaseModel):
    description: str


class SuggestRequirementResponse(BaseModel):
    ai_available: bool
    title: str = ""
    description: str = ""
    platforms: list[str] = []
    priority: str = "medium"
    risk: str = "medium"
    business_rules: list[str] = []


@router.post("/suggest-requirement", response_model=SuggestRequirementResponse)
def suggest_requirement(payload: SuggestRequirementRequest) -> SuggestRequirementResponse:
    result = _service.suggest_requirement(payload.description)
    if not result:
        return SuggestRequirementResponse(ai_available=_service.available)
    return SuggestRequirementResponse(
        ai_available=_service.available,
        title=result.get("title", ""),
        description=result.get("description", ""),
        platforms=result.get("platforms", []),
        priority=result.get("priority", "medium"),
        risk=result.get("risk", "medium"),
        business_rules=result.get("business_rules", []),
    )

