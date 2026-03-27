from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])
_service = AIService()


def _normalize_api_key(raw_key: str | None) -> str | None:
    if raw_key is None:
        return None
    key = raw_key.strip()
    if not key:
        return None
    if len(key) > 512:
        raise HTTPException(status_code=400, detail="Invalid API key header")
    return key


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
def suggest_requirement(
    payload: SuggestRequirementRequest,
    x_openai_api_key: str | None = Header(default=None),
) -> SuggestRequirementResponse:
    api_key = _normalize_api_key(x_openai_api_key)
    result = _service.suggest_requirement(payload.description, api_key=api_key)
    if not result:
        return SuggestRequirementResponse(ai_available=_service.available_for(api_key))
    return SuggestRequirementResponse(
        ai_available=_service.available_for(api_key),
        title=result.get("title", ""),
        description=result.get("description", ""),
        platforms=result.get("platforms", []),
        priority=result.get("priority", "medium"),
        risk=result.get("risk", "medium"),
        business_rules=result.get("business_rules", []),
    )

