"""充电桩管理服务。

负责充电桩启停、故障状态、功率校正、统计报表和 MySQL 同步。
"""

from datetime import datetime, timedelta

from config.settings import FAST_PILES, PILE_POWER, SLOW_PILES
from models.charging_pile import ChargingPile
from repositories.pile_repository import PileRepository


class PileManagementService:
    """维护站内所有充电桩的当前状态。

    默认配置来自 `settings.py`；MySQL 可用时加载数据库状态，不可用时使用内存默认桩。
    """

    def __init__(self):
        self.piles: dict[str, ChargingPile] = {}
        self.repository = PileRepository()
        for pile_id in FAST_PILES:
            self.piles[pile_id] = ChargingPile(pile_id, "fast", PILE_POWER[pile_id])
        for pile_id in SLOW_PILES:
            self.piles[pile_id] = ChargingPile(pile_id, "slow", PILE_POWER[pile_id])
        self._load_piles_from_database()

    def get_pile(self, pile_id: str) -> ChargingPile | None:
        pile = self._get_pile_from_database(pile_id)
        if pile:
            self._normalize_pile_power(pile)
            self.piles[pile.pile_id] = pile
            return pile
        return self.piles.get(pile_id)

    def list_piles(self):
        self._load_piles_from_database()
        return list(self.piles.values())

    def power_on(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.power_on()
        self._save_pile_to_database(pile)
        return pile

    def power_off(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.power_off()
        self._save_pile_to_database(pile)
        return pile

    def start_pile(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.start()
        self._save_pile_to_database(pile)
        return pile

    def set_parameters(self, pile_id: str, parameters: dict):
        pile = self._require_pile(pile_id)
        pile.update_parameters(parameters)
        self._save_pile_to_database(pile)
        return pile

    def mark_charging(self, pile_id: str, session_id: str):
        pile = self._require_pile(pile_id)
        pile.mark_charging(session_id)
        self._save_pile_to_database(pile)
        return pile

    def mark_available(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.mark_available()
        self._save_pile_to_database(pile)
        return pile

    def mark_fault(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.mark_fault()
        self._save_pile_to_database(pile)
        return pile

    def add_statistics(self, pile_id: str, energy: float, hours: float):
        pile = self._require_pile(pile_id)
        pile.add_statistics(energy, hours)
        self._save_pile_to_database(pile)
        return pile

    def available_piles_by_mode(self, mode: str):
        return [
            pile for pile in self.piles.values()
            if pile.pile_type == mode and pile.is_enabled and pile.status in ("ACTIVE", "CHARGING")
        ]

    def get_statistics(self):
        total = len(self.piles)
        active = sum(1 for pile in self.piles.values() if pile.is_enabled)
        charging = sum(1 for pile in self.piles.values() if pile.status == "CHARGING")
        return {
            "activePiles": active,
            "totalPiles": total,
            "chargingPiles": charging,
            "offlinePiles": total - active,
        }

    def get_reports(self):
        """管理员统计报表，支持 day/week/month/all 四种时间范围。"""
        time_range = self._get_report_time_range()
        bills = self._filter_bills_by_time_range(self._list_report_bills(), time_range)
        bills_by_pile = {}
        for bill in bills:
            bills_by_pile.setdefault(bill.pile_id, []).append(bill)

        return [
            self._build_report_row(index + 1, pile, bills_by_pile.get(pile.pile_id, []), time_range)
            for index, pile in enumerate(self.list_piles())
        ]

    @staticmethod
    def _build_report_row(index: int, pile: ChargingPile, bills: list, time_range: str):
        charge_count = len(bills)
        charge_duration = round(sum(bill.duration_hours() for bill in bills), 2)
        energy_amount = round(sum(bill.energy_amount for bill in bills), 2)
        charge_fee = round(sum(bill.charge_fee for bill in bills), 2)
        service_fee = round(sum(bill.service_fee for bill in bills), 2)
        total_fee = round(sum(bill.total_fee for bill in bills), 2)
        return {
            "id": index,
            "pileId": pile.pile_id,
            "pileName": pile.pile_id,
            "timeRange": time_range,
            "chargeCount": charge_count,
            "chargeDuration": charge_duration,
            "energyAmount": energy_amount,
            "chargeFee": charge_fee,
            "serviceFee": service_fee,
            "totalFee": total_fee,
            "totalCharges": charge_count,
            "totalHours": charge_duration,
            "totalEnergy": energy_amount,
        }

    def _require_pile(self, pile_id: str):
        pile = self.get_pile(pile_id)
        if not pile:
            raise ValueError("pile not found")
        return pile

    def _load_piles_from_database(self):
        try:
            for pile in self.repository.list_piles():
                self._normalize_pile_power(pile)
                self.piles[pile.pile_id] = pile
        except Exception:
            pass

    def _get_pile_from_database(self, pile_id: str) -> ChargingPile | None:
        try:
            return self.repository.get_pile(pile_id)
        except Exception:
            return None

    def _save_pile_to_database(self, pile: ChargingPile):
        try:
            self.repository.save_pile(pile)
        except Exception:
            pass

    def _normalize_pile_power(self, pile: ChargingPile):
        """按需求书配置校正充电桩功率，避免旧数据库数据覆盖当前配置。"""
        expected_power = PILE_POWER.get(pile.pile_id)
        if expected_power is None or pile.power == expected_power:
            return
        pile.power = expected_power
        self._save_pile_to_database(pile)

    @staticmethod
    def _get_report_time_range():
        try:
            from flask import request
            value = request.args.get("timeRange", "all")
        except RuntimeError:
            value = "all"
        return value if value in ("day", "week", "month", "all") else "all"

    @staticmethod
    def _list_report_bills():
        from services.billing_service import billing_service
        return billing_service.list_all_bills()

    @staticmethod
    def _filter_bills_by_time_range(bills: list, time_range: str):
        if time_range == "all":
            return bills

        now = datetime.now()
        if time_range == "day":
            start = datetime(now.year, now.month, now.day)
        elif time_range == "week":
            today = datetime(now.year, now.month, now.day)
            start = today - timedelta(days=today.weekday())
        else:
            start = datetime(now.year, now.month, 1)

        return [bill for bill in bills if bill.created_at >= start]


pile_management_service = PileManagementService()
