"""Initialize the SmartCharge MySQL database schema."""

from __future__ import annotations

from pathlib import Path

try:
    from database.db import db_cursor
except ImportError:
    from db import db_cursor

try:
    from config.settings import PILE_QUEUE_CAPACITY
except ImportError:
    PILE_QUEUE_CAPACITY = 3


SCHEMA_PATH = Path(__file__).with_name("schema.sql")
BATTERY_CAPACITY_COLUMN = "`battery_capacity` DECIMAL(10, 3) NOT NULL DEFAULT 0"


def _split_sql(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    previous = ""

    for char in sql_text:
        if char == "'" and not in_double_quote and previous != "\\":
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote and previous != "\\":
            in_double_quote = not in_double_quote

        if char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        previous = char

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def init_database():
    sql_text = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = _split_sql(sql_text)

    with db_cursor(commit=True, include_database=False) as cursor:
        for statement in statements:
            cursor.execute(statement)

    return {
        "initialized": True,
        "mode": "mysql",
        "schema": str(SCHEMA_PATH),
        "statements": len(statements),
    }


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = %s
        """,
        (table_name, column_name),
    )
    row = cursor.fetchone()
    return bool(row and row.get("count", 0) > 0)


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = %s
        """,
        (table_name,),
    )
    row = cursor.fetchone()
    return bool(row and row.get("count", 0) > 0)


def _add_column_if_missing(cursor, table_name: str, column_name: str, column_sql: str):
    if not _table_exists(cursor, table_name) or _column_exists(cursor, table_name, column_name):
        return False
    cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {column_sql}")
    return True


def run_migrations():
    """Run small idempotent schema migrations for existing databases."""
    applied = []
    with db_cursor(commit=True) as cursor:
        if _add_column_if_missing(cursor, "charging_requests", "battery_capacity", BATTERY_CAPACITY_COLUMN):
            applied.append("charging_requests.battery_capacity")
        if _add_column_if_missing(cursor, "waiting_cars", "battery_capacity", BATTERY_CAPACITY_COLUMN):
            applied.append("waiting_cars.battery_capacity")
        if _table_exists(cursor, "pile_queues"):
            cursor.execute("UPDATE pile_queues SET capacity = %s", (PILE_QUEUE_CAPACITY,))
            applied.append("pile_queues.capacity")
    return {
        "migrated": True,
        "applied": applied,
    }


if __name__ == "__main__":
    result = init_database()
    print(result)
