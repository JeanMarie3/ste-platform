from app.repositories.sqlite_store import RequirementRepository
from app.schemas.common import utc_now
from app.schemas.requirements import RequirementCreate, RequirementRead


class RequirementService:
    def __init__(self) -> None:
        self.repository = RequirementRepository()

    def create_requirement(self, payload: RequirementCreate) -> RequirementRead:
        now = utc_now()
        normalized_project_code = payload.project_code.strip().upper()
        sequence = self.repository.next_sequence_for_project(normalized_project_code)
        requirement_id = f"REQ-{normalized_project_code}-{sequence:04d}"
        payload_data = payload.model_dump()
        payload_data["project_code"] = normalized_project_code

        item = RequirementRead(
            id=requirement_id,
            status="created",
            created_at=now,
            updated_at=now,
            **payload_data,
        )
        return self.repository.create(item)

    def list_requirements(self) -> list[RequirementRead]:
        return self.repository.list()

    def get_requirement(self, requirement_id: str) -> RequirementRead | None:
        return self.repository.get(requirement_id)

    def delete_requirement(self, requirement_id: str) -> bool:
        from app.repositories.sqlite_store import TestCaseRepository
        TestCaseRepository().delete_by_requirement_id(requirement_id)
        return self.repository.delete(requirement_id)
