"""Database placeholder.

The first version uses in-memory services. This module is reserved for a later
SQLite/MySQL implementation.
"""


def get_database_status():
    return {"mode": "memory", "connected": False}

