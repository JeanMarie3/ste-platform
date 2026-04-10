from datetime import datetime

from app.core.database import dumps_json, get_connection, loads_json
from app.schemas.auth import UserPublic, UserRecord
from app.schemas.requirements import RequirementRead
from app.schemas.testcases import TestCaseRead, TestRunRead


class RequirementRepository:
    def create(self, item: RequirementRead) -> RequirementRead:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO requirements (id, title, description, platforms_json, priority, risk, business_rules_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.title,
                    item.description,
                    dumps_json([platform.value for platform in item.platforms]),
                    item.priority,
                    item.risk,
                    dumps_json(item.business_rules),
                    item.status,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                ),
            )
        return item

    def list(self) -> list[RequirementRead]:
        with get_connection() as connection:
            rows = connection.execute("SELECT * FROM requirements ORDER BY created_at DESC").fetchall()
        return [self._map(row) for row in rows]

    def get(self, requirement_id: str) -> RequirementRead | None:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
        return self._map(row) if row else None

    def next_sequence_for_project(self, project_code: str) -> int:
        prefix = f"REQ-{project_code.upper()}-"
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM requirements WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
                (f"{prefix}%",),
            ).fetchone()

            if not row:
                return 1

            try:
                seq_str = row["id"].split("-")[-1]
                return int(seq_str) + 1
            except ValueError:
                return 1

    def delete(self, requirement_id: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM requirements WHERE id = ?", (requirement_id,))
            connection.commit()
            return cursor.rowcount > 0

    def _map(self, row) -> RequirementRead:
        return RequirementRead(
            id=row["id"],
            project_code=self._extract_project_code(row["id"]),
            title=row["title"],
            description=row["description"],
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
        with get_connection() as connection:
            connection.executemany(
                """
                INSERT INTO test_cases (id, requirement_id, title, objective, platform, priority, review_status, steps_json, assertions_json, tags_json, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        item.requirement_id,
                        item.title,
                        item.objective,
                        item.platform.value,
                        item.priority,
                        item.review_status.value,
                        dumps_json([step.model_dump() for step in item.steps]),
                        dumps_json([rule.model_dump() for rule in item.assertions]),
                        dumps_json(item.tags),
                        dumps_json(item.metadata),
                        item.created_at.isoformat(),
                        item.updated_at.isoformat(),
                    )
                    for item in items
                ],
            )
        return items

    def list(self) -> list[TestCaseRead]:
        with get_connection() as connection:
            rows = connection.execute("SELECT * FROM test_cases ORDER BY created_at DESC").fetchall()
        return [self._map(row) for row in rows]

    def get(self, test_case_id: str) -> TestCaseRead | None:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM test_cases WHERE id = ?", (test_case_id,)).fetchone()
        return self._map(row) if row else None

    def update(self, item: TestCaseRead) -> TestCaseRead:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE test_cases
                SET review_status = ?, metadata_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (item.review_status.value, dumps_json(item.metadata), item.updated_at.isoformat(), item.id),
            )
        return item

    def delete_by_requirement_id(self, requirement_id: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM test_cases WHERE requirement_id = ?", (requirement_id,))
        return cursor.rowcount > 0

    def delete(self, test_case_id: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM test_cases WHERE id = ?", (test_case_id,))
        return cursor.rowcount > 0

    def _map(self, row) -> TestCaseRead:
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
                """
                INSERT INTO test_runs (id, test_case_id, agent_type, environment, run_mode, status, summary_reason, confidence_score, started_at, finished_at, steps_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.test_case_id,
                    item.agent_type.value,
                    item.environment,
                    item.run_mode,
                    item.status.value,
                    item.summary_reason,
                    item.confidence_score,
                    item.started_at.isoformat(),
                    item.finished_at.isoformat() if item.finished_at else None,
                    dumps_json([step.model_dump() for step in item.steps]),
                ),
            )
        return item

    def list(self) -> list[TestRunRead]:
        with get_connection() as connection:
            rows = connection.execute("SELECT * FROM test_runs ORDER BY started_at DESC").fetchall()
        return [self._map(row) for row in rows]

    def get(self, run_id: str) -> TestRunRead | None:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM test_runs WHERE id = ?", (run_id,)).fetchone()
        return self._map(row) if row else None

    def delete(self, run_id: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM test_runs WHERE id = ?", (run_id,))
        return cursor.rowcount > 0

    def delete_by_test_case_id(self, test_case_id: str) -> int:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM test_runs WHERE test_case_id = ?", (test_case_id,))
        return cursor.rowcount

    def _map(self, row) -> TestRunRead:
        return TestRunRead(
            id=row["id"],
            test_case_id=row["test_case_id"],
            agent_type=row["agent_type"],
            environment=row["environment"],
            run_mode=row["run_mode"] if "run_mode" in row.keys() else "headless",
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
                """
                INSERT INTO users (id, username, email, password_hash, password_salt, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.username,
                    item.email,
                    item.password_hash,
                    item.password_salt,
                    item.role,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                ),
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
            rows = connection.execute("SELECT id, username, email, role, created_at, updated_at FROM users ORDER BY created_at ASC").fetchall()
        return [self._map_public_row(row) for row in rows]

    def get_by_username(self, username: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return self._map_record_row(row) if row else None

    def get_by_email(self, email: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return self._map_record_row(row) if row else None

    def get_by_username_and_email(self, username: str, email: str) -> UserRecord | None:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE username = ? AND email = ?", (username, email)).fetchone()
        return self._map_record_row(row) if row else None

    def update_password(self, user_id: str, password_hash: str, password_salt: str, updated_at: datetime) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                "UPDATE users SET password_hash = ?, password_salt = ?, updated_at = ? WHERE id = ?",
                (password_hash, password_salt, updated_at.isoformat(), user_id),
            )
        return cursor.rowcount > 0

    def count_by_role(self, role: str) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(1) AS total FROM users WHERE role = ?", (role,)).fetchone()
        return int(row["total"]) if row else 0

    def delete_by_id(self, user_id: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

    def _map_public_row(self, row) -> UserPublic:
        return UserPublic(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=row["role"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _map_record_row(self, row) -> UserRecord:
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

