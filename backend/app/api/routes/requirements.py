from fastapi import APIRouter, HTTPException

from app.schemas.requirements import RequirementCreate, RequirementRead
from app.schemas.testcases import TestCaseRead
from app.services.requirement_service import RequirementService
from app.services.testcase_service import TestCaseService

router = APIRouter(prefix="/requirements", tags=["requirements"])
requirement_service = RequirementService()
testcase_service = TestCaseService()


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


@router.post("/{requirement_id}/generate-testcases", response_model=list[TestCaseRead])
def generate_test_cases(requirement_id: str) -> list[TestCaseRead]:
    requirement = requirement_service.get_requirement(requirement_id)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return testcase_service.generate_for_requirement(requirement)
