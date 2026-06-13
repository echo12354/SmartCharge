"""MySQL connection helpers for SmartCharge.

The current business services still use in-memory state. This module only
provides database connectivity for the first MySQL integration phase.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator


DEFAULT_DB_CONFIG = {
    "host": os.getenv("SMARTCHARGE_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("SMARTCHARGE_DB_PORT", "3306")),
    "user": os.getenv("SMARTCHARGE_DB_USER", "root"),
    "password": os.getenv("SMARTCHARGE_DB_PASSWORD", ""),
    "database": os.getenv("SMARTCHARGE_DB_NAME", "smartcharge"),
    "charset": "utf8mb4",
    "autocommit": False,
}


def _load_driver():
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("PyMySQL is required. Install it with: pip install pymysql") from exc
    return pymysql


def get_db_config(include_database: bool = True) -> dict[str, Any]:
    config = dict(DEFAULT_DB_CONFIG)
    if not include_database:
        config.pop("database", None)
    return config


def get_connection(include_database: bool = True):
    pymysql = _load_driver()
    return pymysql.connect(
        **get_db_config(include_database=include_database),
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextmanager
def db_cursor(commit: bool = False, include_database: bool = True) -> Iterator[Any]:
    connection = get_connection(include_database=include_database)
    try:
        with connection.cursor() as cursor:
            yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_database_status():
    config = get_db_config()
    status = {
        "mode": "mysql",
        "connected": False,
        "database": config["database"],
        "host": config["host"],
        "port": config["port"],
    }
    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            row = cursor.fetchone()
        status["connected"] = bool(row and row.get("ok") == 1)
    except Exception as exc:
        status["error"] = str(exc)
    return status
