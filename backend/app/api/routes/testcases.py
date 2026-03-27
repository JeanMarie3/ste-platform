from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.testcases import ReviewAction, TestCaseRead
from app.services.testcase_service import TestCaseService

router = APIRouter(prefix="/testcases", tags=["testcases"])
service = TestCaseService()


@router.get("", response_model=list[TestCaseRead])
def list_test_cases() -> list[TestCaseRead]:
    return service.list_test_cases()


@router.get("/{test_case_id}", response_model=TestCaseRead)
def get_test_case(test_case_id: str) -> TestCaseRead:
    item = service.get_test_case(test_case_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return item


@router.post("/{test_case_id}/review", response_model=TestCaseRead)
def review_test_case(test_case_id: str, action: ReviewAction) -> TestCaseRead:
    item = service.review_test_case(test_case_id, action)
    if item is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return item


@router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(test_case_id: str) -> Response:
    deleted = service.delete_test_case(test_case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test case not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

