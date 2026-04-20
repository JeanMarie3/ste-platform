from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import text

from app.core.database import dumps_json, get_connection, loads_json
from app.schemas.auth import UserPublic, UserRecord
from app.schemas.requirements import RequirementRead
from app.schemas.testcases import TestCaseRead, TestRunRead


class RequirementRepository:
    def create(self, item: RequirementRead) -> RequirementRead:
        with get_connection() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO requirements (id, title, description, target_url, platforms_json, priority, risk, business_rules_json, status, created_at, updated_at)
                    VALUES (:id, :title, :description, :target_url, :platforms_json, :priority, :risk, :business_rules_json, :status, :created_at, :updated_at)
                    """
                ),
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "target_url": item.target_url,
                    "platforms_json": dumps_json([platform.value for platform in item.platforms]),
                    "priority": item.priority,
                    "risk": item.risk,
                    "business_rules_json": dumps_json(item.business_rules),
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                },
            )
        return item

    def list(self) -> list[RequirementRead]:
        with get_connection() as connection:
            rows = connection.execute(text("SELECT * FROM requirements ORDER BY created_at DESC")).mappings().all()
        return [self._map(row) for row in rows]

    def get(self, requirement_id: str) -> RequirementRead | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM requirements WHERE id = :requirement_id"),
                {"requirement_id": requirement_id},
            ).mappings().first()
        return self._map(row) if row else None

    def next_sequence_for_project(self, project_code: str) -> int:
        prefix = f"REQ-{project_code.upper()}-"
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT id FROM requirements WHERE id LIKE :id_prefix ORDER BY id DESC LIMIT 1"),
                {"id_prefix": f"{prefix}%"},
            ).mappings().first()

            if not row:
                return 1

            try:
                seq_str = row["id"].split("-")[-1]
                return int(seq_str) + 1
            except ValueError:
                return 1

    def delete(self, requirement_id: str) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text("DELETE FROM requirements WHERE id = :requirement_id"),
                {"requirement_id": requirement_id},
            )
            return result.rowcount > 0

    def update(self, item: RequirementRead) -> RequirementRead:
        with get_connection() as connection:
            connection.execute(
                text(
                    """
                    UPDATE requirements
                    SET title = :title,
                        description = :description,
                        target_url = :target_url,
                        platforms_json = :platforms_json,
                        priority = :priority,
                        risk = :risk,
                        business_rules_json = :business_rules_json,
                        status = :status,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "target_url": item.target_url,
                    "platforms_json": dumps_json([platform.value for platform in item.platforms]),
                    "priority": item.priority,
                    "risk": item.risk,
                    "business_rules_json": dumps_json(item.business_rules),
                    "status": item.status,
                    "updated_at": item.updated_at.isoformat(),
                },
            )
        return item

    def _map(self, row: Mapping[str, Any]) -> RequirementRead:
        return RequirementRead(
            id=row["id"],
            project_code=self._extract_project_code(row["id"]),
            title=row["title"],
            description=row["description"],
            target_url=row.get("target_url"),
            platforms=loads_json(row["platforms_json"]),
            priority=row["priority"],
            risk=row["risk"],
            business_rules=loads_json(row["business_rules_json"]),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _extract_project_code(self, requirement_id: str) -> str:
        parts = requirement_id.split("-")
        if len(parts) >= 3 and parts[0] == "REQ":
            return parts[1]
        return "LEGACY"


class TestCaseRepository:
    def create_many(self, items: list[TestCaseRead]) -> list[TestCaseRead]:
        params = [
            {
                "id": item.id,
                "requirement_id": item.requirement_id,
                "title": item.title,
                "objective": item.objective,
                "platform": item.platform.value,
                "priority": item.priority,
                "review_status": item.review_status.value,
                "steps_json": dumps_json([step.model_dump() for step in item.steps]),
                "assertions_json": dumps_json([rule.model_dump() for rule in item.assertions]),
                "tags_json": dumps_json(item.tags),
                "metadata_json": dumps_json(item.metadata),
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in items
        ]
        with get_connection() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO test_cases (id, requirement_id, title, objective, platform, priority, review_status, steps_json, assertions_json, tags_json, metadata_json, created_at, updated_at)
                    VALUES (:id, :requirement_id, :title, :objective, :platform, :priority, :review_status, :steps_json, :assertions_json, :tags_json, :metadata_json, :created_at, :updated_at)
                    """
                ),
                params,
            )
        return items

    def list(self) -> list[TestCaseRead]:
        with get_connection() as connection:
            rows = connection.execute(text("SELECT * FROM test_cases ORDER BY created_at DESC")).mappings().all()
        return [self._map(row) for row in rows]

    def get(self, test_case_id: str) -> TestCaseRead | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM test_cases WHERE id = :test_case_id"),
                {"test_case_id": test_case_id},
            ).mappings().first()
        return self._map(row) if row else None

    def update(self, item: TestCaseRead) -> TestCaseRead:
        with get_connection() as connection:
            connection.execute(
                text(
                    """
                    UPDATE test_cases
                    SET title = :title,
                        objective = :objective,
                        priority = :priority,
                        review_status = :review_status,
                        steps_json = :steps_json,
                        assertions_json = :assertions_json,
                        tags_json = :tags_json,
                        metadata_json = :metadata_json,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "title": item.title,
                    "objective": item.objective,
                    "priority": item.priority,
                    "review_status": item.review_status.value,
                    "steps_json": dumps_json([step.model_dump() for step in item.steps]),
                    "assertions_json": dumps_json([rule.model_dump() for rule in item.assertions]),
                    "tags_json": dumps_json(item.tags),
                    "metadata_json": dumps_json(item.metadata),
                    "updated_at": item.updated_at.isoformat(),
                    "id": item.id,
                },
            )
        return item

    def delete_by_requirement_id(self, requirement_id: str) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text("DELETE FROM test_cases WHERE requirement_id = :requirement_id"),
                {"requirement_id": requirement_id},
            )
        return result.rowcount > 0

    def delete(self, test_case_id: str) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text("DELETE FROM test_cases WHERE id = :test_case_id"),
                {"test_case_id": test_case_id},
            )
        return result.rowcount > 0

    def _map(self, row: Mapping[str, Any]) -> TestCaseRead:
        return TestCaseRead(
            id=row["id"],
            requirement_id=row["requirement_id"],
            title=row["title"],
            objective=row["objective"],
            platform=row["platform"],
            priority=row["priority"],
            review_status=row["review_status"],
            steps=loads_json(row["steps_json"]),
            assertions=loads_json(row["assertions_json"]),
            tags=loads_json(row["tags_json"]),
            metadata=loads_json(row["metadata_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


class TestRunRepository:
    def create(self, item: TestRunRead) -> TestRunRead:
        with get_connection() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO test_runs (id, test_case_id, agent_type, environment, run_mode, status, summary_reason, confidence_score, started_at, finished_at, steps_json)
                    VALUES (:id, :test_case_id, :agent_type, :environment, :run_mode, :status, :summary_reason, :confidence_score, :started_at, :finished_at, :steps_json)
                    """
                ),
                {
                    "id": item.id,
                    "test_case_id": item.test_case_id,
                    "agent_type": item.agent_type.value,
                    "environment": item.environment,
                    "run_mode": item.run_mode,
                    "status": item.status.value,
                    "summary_reason": item.summary_reason,
                    "confidence_score": item.confidence_score,
                    "started_at": item.started_at.isoformat(),
                    "finished_at": item.finished_at.isoformat() if item.finished_at else None,
                    "steps_json": dumps_json([step.model_dump() for step in item.steps]),
                },
            )
        return item

    def list(self) -> list[TestRunRead]:
        with get_connection() as connection:
            rows = connection.execute(text("SELECT * FROM test_runs ORDER BY started_at DESC")).mappings().all()
        return [self._map(row) for row in rows]

    def get(self, run_id: str) -> TestRunRead | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM test_runs WHERE id = :run_id"),
                {"run_id": run_id},
            ).mappings().first()
        return self._map(row) if row else None

    def delete(self, run_id: str) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text("DELETE FROM test_runs WHERE id = :run_id"),
                {"run_id": run_id},
            )
        return result.rowcount > 0

    def delete_by_test_case_id(self, test_case_id: str) -> int:
        with get_connection() as connection:
            result = connection.execute(
                text("DELETE FROM test_runs WHERE test_case_id = :test_case_id"),
                {"test_case_id": test_case_id},
            )
        return result.rowcount

    def update_result(self, item: TestRunRead) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE test_runs
                    SET status = :status,
                        summary_reason = :summary_reason,
                        confidence_score = :confidence_score,
                        finished_at = :finished_at,
                        steps_json = :steps_json
                    WHERE id = :id
                    """
                ),
                {
                    "id": item.id,
                    "status": item.status.value,
                    "summary_reason": item.summary_reason,
                    "confidence_score": item.confidence_score,
                    "finished_at": item.finished_at.isoformat() if item.finished_at else None,
                    "steps_json": dumps_json([step.model_dump() for step in item.steps]),
                },
            )
        return result.rowcount > 0

    def _map(self, row: Mapping[str, Any]) -> TestRunRead:
        return TestRunRead(
            id=row["id"],
            test_case_id=row["test_case_id"],
            agent_type=row["agent_type"],
            environment=row["environment"],
            run_mode=row.get("run_mode") or "headless",
            status=row["status"],
            summary_reason=row["summary_reason"],
            confidence_score=row["confidence_score"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            steps=loads_json(row["steps_json"]),
        )


class AuthRepository:
    def create(self, item: UserRecord) -> UserPublic:
        with get_connection() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO users (id, username, email, password_hash, password_salt, role, created_at, updated_at)
                    VALUES (:id, :username, :email, :password_hash, :password_salt, :role, :created_at, :updated_at)
                    """
                ),
                {
                    "id": item.id,
                    "username": item.username,
                    "email": item.email,
                    "password_hash": item.password_hash,
                    "password_salt": item.password_salt,
                    "role": item.role,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                },
            )
        return self._map_public_row(
            {
                "id": item.id,
                "username": item.username,
                "email": item.email,
                "role": item.role,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
        )

    def list(self) -> list[UserPublic]:
        with get_connection() as connection:
            rows = connection.execute(
                text("SELECT id, username, email, role, created_at, updated_at FROM users ORDER BY created_at ASC")
            ).mappings().all()
        return [self._map_public_row(row) for row in rows]

    def get_by_username(self, username: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM users WHERE username = :username"),
                {"username": username},
            ).mappings().first()
        return self._map_record_row(row) if row else None

    def get_by_id(self, user_id: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM users WHERE id = :user_id"),
                {"user_id": user_id},
            ).mappings().first()
        return self._map_record_row(row) if row else None

    def get_by_email(self, email: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email},
            ).mappings().first()
        return self._map_record_row(row) if row else None

    def get_by_username_and_email(self, username: str, email: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT * FROM users WHERE username = :username AND email = :email"),
                {"username": username, "email": email},
            ).mappings().first()
        return self._map_record_row(row) if row else None

    def update_password(self, user_id: str, password_hash: str, password_salt: str, updated_at: datetime) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text("UPDATE users SET password_hash = :password_hash, password_salt = :password_salt, updated_at = :updated_at WHERE id = :user_id"),
                {
                    "password_hash": password_hash,
                    "password_salt": password_salt,
                    "updated_at": updated_at.isoformat(),
                    "user_id": user_id,
                },
            )
        return result.rowcount > 0

    def count_by_role(self, role: str) -> int:
        with get_connection() as connection:
            row = connection.execute(
                text("SELECT COUNT(1) AS total FROM users WHERE role = :role"),
                {"role": role},
            ).mappings().first()
        return int(row["total"]) if row else 0

    def delete_by_id(self, user_id: str) -> bool:
        with get_connection() as connection:
            result = connection.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": user_id},
            )
        return result.rowcount > 0

    def _map_public_row(self, row: Mapping[str, Any]) -> UserPublic:
        return UserPublic(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=row["role"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _map_record_row(self, row: Mapping[str, Any]) -> UserRecord:
        return UserRecord(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=row["role"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
        )

