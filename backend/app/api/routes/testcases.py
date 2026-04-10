import json

from fastapi import APIRouter, Body, HTTPException, Response, status
from pydantic import ValidationError

from app.schemas.testcases import ReviewAction, TestCaseRead, TestCaseUpdate
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


@router.patch("/{test_case_id}", response_model=TestCaseRead)
def update_test_case(test_case_id: str, payload: TestCaseUpdate) -> TestCaseRead:
    item = service.update_test_case(test_case_id, payload)
    if item is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return item


@router.post("/{test_case_id}/review", response_model=TestCaseRead)
def review_test_case(test_case_id: str, action_payload: dict | str = Body(...)) -> TestCaseRead:
    if isinstance(action_payload, str):
        try:
            action_payload = json.loads(action_payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="Invalid JSON body for review action") from exc

    try:
        action = ReviewAction.model_validate(action_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

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

