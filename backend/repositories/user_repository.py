"""MySQL repository for users."""

from __future__ import annotations

from models.user import User
from database.db import db_cursor


class UserRepository:
    def list_users(self) -> list[User]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT username, password, role, created_at, last_login
                FROM users
                ORDER BY created_at ASC, username ASC
                """
            )
            return [self._row_to_user(row) for row in cursor.fetchall()]

    def get_user(self, username: str) -> User | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT username, password, role, created_at, last_login
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def create_user(self, user: User) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password, role, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user.username, user.password, user.role, user.created_at, user.last_login),
            )

    def update_last_login(self, username: str, last_login) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET last_login = %s
                WHERE username = %s
                """,
                (last_login, username),
            )

    @staticmethod
    def _row_to_user(row: dict) -> User:
        return User(
            username=row["username"],
            password=row["password"],
            role=row["role"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )
