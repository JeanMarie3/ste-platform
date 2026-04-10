from app.repositories.sql_store import RequirementRepository
from app.domain.enums import PlatformType
from app.schemas.common import utc_now
from app.schemas.requirements import RequirementCreate, RequirementRead, RequirementUpdate


class RequirementService:
    def __init__(self) -> None:
        self.repository = RequirementRepository()

    def create_requirement(self, payload: RequirementCreate) -> RequirementRead:
        now = utc_now()
        normalized_project_code = payload.project_code.strip().upper()
        if PlatformType.WEB in payload.platforms and not payload.target_url:
            raise ValueError("target_url is required when web platform is selected")
        sequence = self.repository.next_sequence_for_project(normalized_project_code)
        requirement_id = f"REQ-{normalized_project_code}-{sequence:04d}"
        payload_data = payload.model_dump()
        payload_data["project_code"] = normalized_project_code
        payload_data["target_url"] = payload.target_url.strip() if payload.target_url else None

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

    def update_requirement(self, requirement_id: str, payload: RequirementUpdate) -> RequirementRead | None:
        current = self.repository.get(requirement_id)
        if current is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        merged_platforms = updates.get("platforms", current.platforms)
        merged_target_url = updates.get("target_url", current.target_url)
        if PlatformType.WEB in merged_platforms and not merged_target_url:
            raise ValueError("target_url is required when web platform is selected")

        updated = current.model_copy(
            update={
                **updates,
                "updated_at": utc_now(),
            }
        )
        return self.repository.update(updated)

    def delete_requirement(self, requirement_id: str) -> bool:
        from app.repositories.sql_store import TestCaseRepository
        TestCaseRepository().delete_by_requirement_id(requirement_id)
        return self.repository.delete(requirement_id)
