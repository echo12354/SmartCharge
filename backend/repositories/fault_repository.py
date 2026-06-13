"""故障记录仓储。

故障发生和恢复记录优先写入 MySQL；写入失败时服务层仍保留内存记录用于接口返回。
"""

from __future__ import annotations

import json

from database.db import db_cursor
from models.fault_record import FaultRecord


class FaultRepository:
    """负责 `fault_records` 表和 `FaultRecord` 模型之间的转换。"""

    def save_record(self, record: FaultRecord) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO fault_records (
                    fault_id, pile_id, reason, affected_car_ids,
                    status, fault_time, recovery_time
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    pile_id = VALUES(pile_id),
                    reason = VALUES(reason),
                    affected_car_ids = VALUES(affected_car_ids),
                    status = VALUES(status),
                    fault_time = VALUES(fault_time),
                    recovery_time = VALUES(recovery_time)
                """,
                self._record_values(record),
            )

    def get_record(self, fault_id: str) -> FaultRecord | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT fault_id, pile_id, reason, affected_car_ids,
                       status, fault_time, recovery_time
                FROM fault_records
                WHERE fault_id = %s
                """,
                (fault_id,),
            )
            row = cursor.fetchone()
            return self._row_to_record(row) if row else None

    def get_latest_by_pile(self, pile_id: str) -> FaultRecord | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT fault_id, pile_id, reason, affected_car_ids,
                       status, fault_time, recovery_time
                FROM fault_records
                WHERE pile_id = %s
                ORDER BY fault_time DESC, fault_id DESC
                LIMIT 1
                """,
                (pile_id,),
            )
            row = cursor.fetchone()
            return self._row_to_record(row) if row else None

    def list_records(self) -> list[FaultRecord]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT fault_id, pile_id, reason, affected_car_ids,
                       status, fault_time, recovery_time
                FROM fault_records
                ORDER BY fault_time DESC, fault_id DESC
                """
            )
            return [self._row_to_record(row) for row in cursor.fetchall()]

    @staticmethod
    def _record_values(record: FaultRecord) -> tuple:
        return (
            record.fault_id,
            record.pile_id,
            record.reason,
            json.dumps(record.affected_car_ids, ensure_ascii=False),
            record.status,
            record.fault_time,
            record.recovery_time,
        )

    @staticmethod
    def _row_to_record(row: dict) -> FaultRecord:
        affected = row.get("affected_car_ids")
        if isinstance(affected, str):
            affected = json.loads(affected) if affected else []
        if affected is None:
            affected = []
        return FaultRecord(
            fault_id=row["fault_id"],
            pile_id=row["pile_id"],
            reason=row["reason"],
            affected_car_ids=affected,
            status=row["status"],
            fault_time=row["fault_time"],
            recovery_time=row["recovery_time"],
        )
