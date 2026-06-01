"""MySQL repository for charging sessions."""

from __future__ import annotations

from database.db import db_cursor
from models.charging_session import ChargingSession


class SessionRepository:
    ACTIVE_STATUSES = ("PREPARING", "CHARGING")

    def save_session(self, session: ChargingSession) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO charging_sessions (
                    session_id, request_id, user_id, pile_id, target_amount,
                    current_amount, pile_power, status, start_time, end_time,
                    stop_reason, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    request_id = VALUES(request_id),
                    user_id = VALUES(user_id),
                    pile_id = VALUES(pile_id),
                    target_amount = VALUES(target_amount),
                    current_amount = VALUES(current_amount),
                    pile_power = VALUES(pile_power),
                    status = VALUES(status),
                    start_time = VALUES(start_time),
                    end_time = VALUES(end_time),
                    stop_reason = VALUES(stop_reason),
                    updated_at = NOW()
                """,
                self._session_values(session),
            )

    def get_session(self, session_id: str) -> ChargingSession | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, request_id, user_id, pile_id, target_amount,
                       current_amount, pile_power, status, start_time, end_time, stop_reason
                FROM charging_sessions
                WHERE session_id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            return self._row_to_session(row) if row else None

    def get_active_session_by_user(self, user_id: str) -> ChargingSession | None:
        return self._get_active_session("user_id", user_id)

    def get_active_session_by_pile(self, pile_id: str) -> ChargingSession | None:
        return self._get_active_session("pile_id", pile_id)

    def list_active_sessions(self) -> list[ChargingSession]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, request_id, user_id, pile_id, target_amount,
                       current_amount, pile_power, status, start_time, end_time, stop_reason
                FROM charging_sessions
                WHERE status IN ('PREPARING', 'CHARGING')
                ORDER BY start_time DESC, session_id DESC
                """
            )
            return [self._row_to_session(row) for row in cursor.fetchall()]

    def list_user_sessions(self, user_id: str) -> list[ChargingSession]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, request_id, user_id, pile_id, target_amount,
                       current_amount, pile_power, status, start_time, end_time, stop_reason
                FROM charging_sessions
                WHERE user_id = %s
                ORDER BY COALESCE(start_time, end_time) DESC, session_id DESC
                """,
                (user_id,),
            )
            return [self._row_to_session(row) for row in cursor.fetchall()]

    def list_all_sessions(self) -> list[ChargingSession]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, request_id, user_id, pile_id, target_amount,
                       current_amount, pile_power, status, start_time, end_time, stop_reason
                FROM charging_sessions
                ORDER BY COALESCE(start_time, end_time) DESC, session_id DESC
                """
            )
            return [self._row_to_session(row) for row in cursor.fetchall()]

    def _get_active_session(self, column: str, value: str) -> ChargingSession | None:
        if column not in ("user_id", "pile_id"):
            raise ValueError("invalid active session column")
        with db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT session_id, request_id, user_id, pile_id, target_amount,
                       current_amount, pile_power, status, start_time, end_time, stop_reason
                FROM charging_sessions
                WHERE {column} = %s
                  AND status IN ('PREPARING', 'CHARGING')
                ORDER BY start_time DESC, session_id DESC
                LIMIT 1
                """,
                (value,),
            )
            row = cursor.fetchone()
            return self._row_to_session(row) if row else None

    @staticmethod
    def _session_values(session: ChargingSession) -> tuple:
        return (
            session.session_id,
            session.request_id,
            session.user_id,
            session.pile_id,
            session.target_amount,
            session.current_amount,
            session.pile_power,
            session.status,
            session.start_time,
            session.end_time,
            session.stop_reason,
        )

    @staticmethod
    def _row_to_session(row: dict) -> ChargingSession:
        return ChargingSession(
            session_id=row["session_id"],
            request_id=row["request_id"],
            user_id=row["user_id"],
            pile_id=row["pile_id"],
            target_amount=float(row["target_amount"]),
            current_amount=float(row["current_amount"]),
            pile_power=float(row["pile_power"]),
            status=row["status"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            stop_reason=row["stop_reason"],
        )
