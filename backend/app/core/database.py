import json
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.core.config import settings


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(settings.sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                platforms_json TEXT NOT NULL,
                priority TEXT NOT NULL,
                risk TEXT NOT NULL,
                business_rules_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_cases (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                title TEXT NOT NULL,
                objective TEXT NOT NULL,
                platform TEXT NOT NULL,
                priority TEXT NOT NULL,
                review_status TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                assertions_json TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(requirement_id) REFERENCES requirements(id)
            );

            CREATE TABLE IF NOT EXISTS test_runs (
                id TEXT PRIMARY KEY,
                test_case_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL,
                summary_reason TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                steps_json TEXT NOT NULL,
                FOREIGN KEY(test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
            );
            """
        )


def dumps_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads_json(value: str) -> object:
    return json.loads(value)
