"""调度决策仓储。

普通调度、优先级调度和时间顺序调度都会尽量写入 MySQL，便于追踪调度原因。
"""

from __future__ import annotations

from database.db import db_cursor
from models.dispatch_decision import DispatchDecision


class DispatchRepository:
    """负责 `dispatch_decisions` 表和 `DispatchDecision` 模型之间的转换。"""

    def save_decision(self, decision: DispatchDecision) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO dispatch_decisions (
                    decision_id, request_id, user_id, selected_pile_id,
                    strategy, reason, expected_completion_hours, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    request_id = VALUES(request_id),
                    user_id = VALUES(user_id),
                    selected_pile_id = VALUES(selected_pile_id),
                    strategy = VALUES(strategy),
                    reason = VALUES(reason),
                    expected_completion_hours = VALUES(expected_completion_hours),
                    created_at = VALUES(created_at)
                """,
                self._decision_values(decision),
            )

    def list_recent_decisions(self, limit: int = 10) -> list[DispatchDecision]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT decision_id, request_id, user_id, selected_pile_id,
                       strategy, reason, expected_completion_hours, created_at
                FROM dispatch_decisions
                ORDER BY created_at DESC, decision_id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [self._row_to_decision(row) for row in reversed(cursor.fetchall())]

    def count_decisions(self) -> int:
        with db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM dispatch_decisions")
            row = cursor.fetchone()
            return int(row["count"]) if row else 0

    @staticmethod
    def _decision_values(decision: DispatchDecision) -> tuple:
        return (
            decision.decision_id,
            decision.request_id,
            decision.user_id,
            decision.selected_pile_id,
            decision.strategy,
            decision.reason,
            decision.expected_completion_hours,
            decision.created_at,
        )

    @staticmethod
    def _row_to_decision(row: dict) -> DispatchDecision:
        return DispatchDecision(
            decision_id=row["decision_id"],
            request_id=row["request_id"],
            user_id=row["user_id"],
            selected_pile_id=row["selected_pile_id"],
            strategy=row["strategy"],
            reason=row["reason"],
            expected_completion_hours=float(row["expected_completion_hours"]),
            created_at=row["created_at"],
        )
