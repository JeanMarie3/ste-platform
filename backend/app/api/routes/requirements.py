from fastapi import APIRouter, Header, HTTPException

from app.schemas.requirements import RequirementCreate, RequirementRead
from app.schemas.testcases import TestCaseRead
from app.services.requirement_service import RequirementService
from app.services.testcase_service import TestCaseService

router = APIRouter(prefix="/requirements", tags=["requirements"])
requirement_service = RequirementService()
testcase_service = TestCaseService()


def _normalize_api_key(raw_key: str | None) -> str | None:
    if raw_key is None:
        return None
    key = raw_key.strip()
    if not key:
        return None
    if len(key) > 512:
        raise HTTPException(status_code=400, detail="Invalid API key header")
    return key


@router.post("", response_model=RequirementRead)
def create_requirement(payload: RequirementCreate) -> RequirementRead:
    return requirement_service.create_requirement(payload)


@router.get("", response_model=list[RequirementRead])
def list_requirements() -> list[RequirementRead]:
    return requirement_service.list_requirements()


@router.get("/{requirement_id}", response_model=RequirementRead)
def get_requirement(requirement_id: str) -> RequirementRead:
    item = requirement_service.get_requirement(requirement_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return item


@router.delete("/{requirement_id}", status_code=204)
def delete_requirement(requirement_id: str) -> None:
    success = requirement_service.delete_requirement(requirement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Requirement not found")


@router.post("/{requirement_id}/generate-testcases", response_model=list[TestCaseRead])
def generate_test_cases(
    requirement_id: str,
    x_openai_api_key: str | None = Header(default=None),
) -> list[TestCaseRead]:
    requirement = requirement_service.get_requirement(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return testcase_service.generate_for_requirement(requirement, api_key=_normalize_api_key(x_openai_api_key))
