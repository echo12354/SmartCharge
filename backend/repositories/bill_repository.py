"""账单仓储。

账单属于验收中的核心持久化数据，查询时优先从 MySQL 读取，内存账单作为兜底。
"""

from __future__ import annotations

from database.db import db_cursor
from models.bill import Bill


class BillRepository:
    """负责 `bills` 表和 `Bill` 模型之间的转换。"""

    def save_bill(self, bill: Bill) -> None:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO bills (
                    bill_id, session_id, user_id, pile_id, energy_amount,
                    start_time, end_time, duration_hours, price_type, unit_price,
                    charge_fee, service_fee, total_fee, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    session_id = VALUES(session_id),
                    user_id = VALUES(user_id),
                    pile_id = VALUES(pile_id),
                    energy_amount = VALUES(energy_amount),
                    start_time = VALUES(start_time),
                    end_time = VALUES(end_time),
                    duration_hours = VALUES(duration_hours),
                    price_type = VALUES(price_type),
                    unit_price = VALUES(unit_price),
                    charge_fee = VALUES(charge_fee),
                    service_fee = VALUES(service_fee),
                    total_fee = VALUES(total_fee),
                    status = VALUES(status)
                """,
                self._bill_values(bill),
            )

    def get_bill(self, bill_id_or_session_id: str) -> Bill | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT bill_id, session_id, user_id, pile_id, energy_amount,
                       start_time, end_time, price_type, unit_price, charge_fee,
                       service_fee, total_fee, status, created_at
                FROM bills
                WHERE bill_id = %s OR session_id = %s
                LIMIT 1
                """,
                (bill_id_or_session_id, bill_id_or_session_id),
            )
            row = cursor.fetchone()
            return self._row_to_bill(row) if row else None

    def list_user_bills(self, user_id: str) -> list[Bill]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT bill_id, session_id, user_id, pile_id, energy_amount,
                       start_time, end_time, price_type, unit_price, charge_fee,
                       service_fee, total_fee, status, created_at
                FROM bills
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            return [self._row_to_bill(row) for row in cursor.fetchall()]

    def list_all_bills(self) -> list[Bill]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT bill_id, session_id, user_id, pile_id, energy_amount,
                       start_time, end_time, price_type, unit_price, charge_fee,
                       service_fee, total_fee, status, created_at
                FROM bills
                ORDER BY created_at DESC
                """
            )
            return [self._row_to_bill(row) for row in cursor.fetchall()]

    @staticmethod
    def _bill_values(bill: Bill) -> tuple:
        return (
            bill.bill_id,
            bill.session_id,
            bill.user_id,
            bill.pile_id,
            bill.energy_amount,
            bill.start_time,
            bill.end_time,
            bill.duration_hours(),
            bill.price_type,
            bill.unit_price,
            bill.charge_fee,
            bill.service_fee,
            bill.total_fee,
            bill.status,
            bill.created_at,
        )

    @staticmethod
    def _row_to_bill(row: dict) -> Bill:
        bill = Bill(
            bill_id=row["bill_id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            pile_id=row["pile_id"],
            energy_amount=float(row["energy_amount"]),
            start_time=row["start_time"],
            end_time=row["end_time"],
            status=row["status"],
            created_at=row["created_at"],
        )
        bill.price_type = row["price_type"]
        bill.unit_price = float(row["unit_price"])
        bill.charge_fee = float(row["charge_fee"])
        bill.service_fee = float(row["service_fee"])
        bill.total_fee = float(row["total_fee"])
        return bill
