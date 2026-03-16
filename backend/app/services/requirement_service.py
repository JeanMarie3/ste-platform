from app.repositories.sqlite_store import RequirementRepository
from app.schemas.common import new_id, utc_now
from app.schemas.requirements import RequirementCreate, RequirementRead


class RequirementService:
    def __init__(self) -> None:
        self.repository = RequirementRepository()

    def create_requirement(self, payload: RequirementCreate) -> RequirementRead:
        now = utc_now()
        item = RequirementRead(
            id=new_id("REQ"),
            status="created",
            created_at=now,
            updated_at=now,
            **payload.model_dump(),
        )
        return self.repository.create(item)

    def list_requirements(self) -> list[RequirementRead]:
        return self.repository.list()

    def get_requirement(self, requirement_id: str) -> RequirementRead | None:
        return self.repository.get(requirement_id)
