import argparse
import sqlite3
from pathlib import Path

from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_connection, initialize_database

TABLES_IN_ORDER: tuple[str, ...] = ("users", "requirements", "test_cases", "test_runs")


def _read_source_rows(sqlite_path: Path, table_name: str) -> list[dict]:
    with sqlite3.connect(sqlite_path) as source:
        source.row_factory = sqlite3.Row
        rows = source.execute(f"SELECT * FROM {table_name}").fetchall()
    return [dict(row) for row in rows]


def _insert_rows(table_name: str, rows: list[dict]) -> int:
    if not rows:
        return 0

    columns = list(rows[0].keys())
    column_sql = ", ".join(columns)
    values_sql = ", ".join(f":{column}" for column in columns)
    statement = text(
        f"INSERT INTO {table_name} ({column_sql}) VALUES ({values_sql}) ON CONFLICT (id) DO NOTHING"
    )

    with get_connection() as connection:
        result = connection.execute(statement, rows)
    return int(result.rowcount or 0)


def migrate(sqlite_path: Path) -> dict[str, int]:
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite source not found: {sqlite_path}")

    initialize_database()

    inserted_counts: dict[str, int] = {}
    for table_name in TABLES_IN_ORDER:
        rows = _read_source_rows(sqlite_path=sqlite_path, table_name=table_name)
        inserted_counts[table_name] = _insert_rows(table_name=table_name, rows=rows)
    return inserted_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate existing SQLite data into the configured DATABASE_URL")
    parser.add_argument(
        "--sqlite-path",
        default=str(settings.sqlite_path),
        help="Path to source SQLite database file (default: backend data ste.db)",
    )
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path).resolve()

    print(f"Target DATABASE_URL: {settings.database_url}")
    print(f"Source SQLite path: {sqlite_path}")

    counts = migrate(sqlite_path)
    print("Migration completed.")
    for table_name in TABLES_IN_ORDER:
        print(f"- {table_name}: inserted {counts.get(table_name, 0)} rows")


if __name__ == "__main__":
    main()

