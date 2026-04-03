import json

from fastapi import APIRouter, Body, HTTPException, Response, status
from pydantic import ValidationError

from app.schemas.executions import StartExecutionRequest
from app.schemas.testcases import TestRunRead
from app.services.execution_service import ExecutionService

router = APIRouter(prefix="/executions", tags=["executions"])
service = ExecutionService()


@router.post("/start", response_model=TestRunRead)
def start_execution(payload_body: dict | str = Body(...)) -> TestRunRead:
    if isinstance(payload_body, str):
        try:
            payload_body = json.loads(payload_body)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="Invalid JSON body for execution request") from exc

    try:
        payload = StartExecutionRequest.model_validate(payload_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    try:
        return service.start_execution(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Test case not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[TestRunRead])
def list_runs() -> list[TestRunRead]:
    return service.list_runs()


@router.get("/{run_id}", response_model=TestRunRead)
def get_run(run_id: str) -> TestRunRead:
    item = service.get_run(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return item


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: str) -> Response:
    deleted = service.delete_run(run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

