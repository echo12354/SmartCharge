"""充电请求仓储。

服务层优先通过这里读写 MySQL；如果数据库不可用，服务层会捕获异常并继续使用内存兜底。
"""

from __future__ import annotations

from database.db import db_cursor
from models.charging_request import ChargingRequest


class RequestRepository:
    """负责 `charging_requests` 表和 `ChargingRequest` 模型之间的转换。"""

    def save_request(self, request: ChargingRequest) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO charging_requests (
                    request_id, user_id, charge_mode, requested_amount, status,
                    queue_number, assigned_pile_id, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    charge_mode = VALUES(charge_mode),
                    requested_amount = VALUES(requested_amount),
                    status = VALUES(status),
                    queue_number = VALUES(queue_number),
                    assigned_pile_id = VALUES(assigned_pile_id),
                    updated_at = VALUES(updated_at)
                """,
                self._request_values(request),
            )

    def get_request(self, request_id: str) -> ChargingRequest | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT request_id, user_id, charge_mode, requested_amount, status,
                       queue_number, assigned_pile_id, created_at, updated_at
                FROM charging_requests
                WHERE request_id = %s
                """,
                (request_id,),
            )
            row = cursor.fetchone()
            return self._row_to_request(row) if row else None

    def get_active_request_by_user(self, user_id: str) -> ChargingRequest | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT request_id, user_id, charge_mode, requested_amount, status,
                       queue_number, assigned_pile_id, created_at, updated_at
                FROM charging_requests
                WHERE user_id = %s
                  AND status NOT IN ('COMPLETED', 'CANCELLED')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return self._row_to_request(row) if row else None

    def list_active_requests(self) -> list[ChargingRequest]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT request_id, user_id, charge_mode, requested_amount, status,
                       queue_number, assigned_pile_id, created_at, updated_at
                FROM charging_requests
                WHERE status NOT IN ('COMPLETED', 'CANCELLED')
                ORDER BY created_at ASC
                """
            )
            return [self._row_to_request(row) for row in cursor.fetchall()]

    @staticmethod
    def _request_values(request: ChargingRequest) -> tuple:
        return (
            request.request_id,
            request.user_id,
            request.charge_mode,
            request.requested_amount,
            request.status,
            request.queue_number,
            request.assigned_pile_id,
            request.created_at,
            request.updated_at,
        )

    @staticmethod
    def _row_to_request(row: dict) -> ChargingRequest:
        return ChargingRequest(
            request_id=row["request_id"],
            user_id=row["user_id"],
            charge_mode=row["charge_mode"],
            requested_amount=float(row["requested_amount"]),
            status=row["status"],
            queue_number=row["queue_number"],
            assigned_pile_id=row["assigned_pile_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
