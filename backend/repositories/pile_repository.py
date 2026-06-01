"""MySQL repository for charging piles."""

from __future__ import annotations

import json

from database.db import db_cursor
from models.charging_pile import ChargingPile


class PileRepository:
    def list_piles(self) -> list[ChargingPile]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT pile_id, pile_type, power, status, is_enabled, parameters,
                       total_sessions, total_energy, total_hours, current_session_id, updated_at
                FROM charging_piles
                ORDER BY pile_id ASC
                """
            )
            return [self._row_to_pile(row) for row in cursor.fetchall()]

    def get_pile(self, pile_id: str) -> ChargingPile | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT pile_id, pile_type, power, status, is_enabled, parameters,
                       total_sessions, total_energy, total_hours, current_session_id, updated_at
                FROM charging_piles
                WHERE pile_id = %s
                """,
                (pile_id,),
            )
            row = cursor.fetchone()
            return self._row_to_pile(row) if row else None

    def save_pile(self, pile: ChargingPile) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO charging_piles (
                    pile_id, pile_type, power, status, is_enabled, parameters,
                    total_sessions, total_energy, total_hours, current_session_id, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    pile_type = VALUES(pile_type),
                    power = VALUES(power),
                    status = VALUES(status),
                    is_enabled = VALUES(is_enabled),
                    parameters = VALUES(parameters),
                    total_sessions = VALUES(total_sessions),
                    total_energy = VALUES(total_energy),
                    total_hours = VALUES(total_hours),
                    current_session_id = VALUES(current_session_id),
                    updated_at = VALUES(updated_at)
                """,
                self._pile_values(pile),
            )

    @staticmethod
    def _pile_values(pile: ChargingPile) -> tuple:
        return (
            pile.pile_id,
            pile.pile_type,
            pile.power,
            pile.status,
            1 if pile.is_enabled else 0,
            json.dumps(pile.parameters, ensure_ascii=False),
            pile.total_sessions,
            pile.total_energy,
            pile.total_hours,
            pile.current_session_id,
            pile.updated_at,
        )

    @staticmethod
    def _row_to_pile(row: dict) -> ChargingPile:
        parameters = row.get("parameters")
        if isinstance(parameters, str):
            parameters = json.loads(parameters) if parameters else {}
        if parameters is None:
            parameters = {}

        return ChargingPile(
            pile_id=row["pile_id"],
            pile_type=row["pile_type"],
            power=float(row["power"]),
            status=row["status"],
            is_enabled=bool(row["is_enabled"]),
            parameters=parameters,
            total_sessions=int(row["total_sessions"]),
            total_energy=float(row["total_energy"]),
            total_hours=float(row["total_hours"]),
            current_session_id=row["current_session_id"],
            updated_at=row["updated_at"],
        )
