"""Initialize the SmartCharge MySQL database schema."""

from __future__ import annotations

from pathlib import Path

from db import db_cursor


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


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


if __name__ == "__main__":
    result = init_database()
    print(result)
