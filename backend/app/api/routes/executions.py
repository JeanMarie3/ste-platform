from fastapi import APIRouter, HTTPException

from app.schemas.executions import StartExecutionRequest
from app.schemas.testcases import TestRunRead
from app.services.execution_service import ExecutionService

router = APIRouter(prefix="/executions", tags=["executions"])
service = ExecutionService()


@router.post("/start", response_model=TestRunRead)
def start_execution(payload: StartExecutionRequest) -> TestRunRead:
    try:
        return service.start_execution(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Test case not found") from exc


@router.get("", response_model=list[TestRunRead])
def list_runs() -> list[TestRunRead]:
    return service.list_runs()


@router.get("/{run_id}", response_model=TestRunRead)
def get_run(run_id: str) -> TestRunRead:
    item = service.get_run(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return item
