from datetime import datetime

from app.core.database import dumps_json, get_connection, loads_json
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
            rows = connection.execute("SELECT id FROM requirements WHERE id LIKE ?", (f"{prefix}%",)).fetchall()

        max_sequence = 0
        for row in rows:
            requirement_id = row["id"]
            if not requirement_id.startswith(prefix):
                continue
            suffix = requirement_id[len(prefix):]
            if suffix.isdigit():
                max_sequence = max(max_sequence, int(suffix))
        return max_sequence + 1

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
                INSERT INTO test_runs (id, test_case_id, agent_type, environment, status, summary_reason, confidence_score, started_at, finished_at, steps_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.test_case_id,
                    item.agent_type.value,
                    item.environment,
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

    def _map(self, row) -> TestRunRead:
        return TestRunRead(
            id=row["id"],
            test_case_id=row["test_case_id"],
            agent_type=row["agent_type"],
            environment=row["environment"],
            status=row["status"],
            summary_reason=row["summary_reason"],
            confidence_score=row["confidence_score"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            steps=loads_json(row["steps_json"]),
        )
