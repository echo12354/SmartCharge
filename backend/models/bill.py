"""账单模型。

一次充电结束后生成一条账单，保存电费、服务费和总费用等详单字段。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from config.settings import NORMAL_PRICE, PEAK_PRICE, SERVICE_FEE_RATE, VALLEY_PRICE
from utils.id_generator import generate_id

# 峰平谷切换时刻（与需求书一致）。
_PRICE_BOUNDARY_HOURS = (7, 10, 15, 18, 21, 23)


@dataclass
class Bill:
    """用户充电详单。

    账单费用由两部分组成：峰平谷电费 + 固定服务费。
    """

    session_id: str
    user_id: str
    pile_id: str
    energy_amount: float
    start_time: datetime
    end_time: datetime
    status: str
    pile_power: float | None = None
    bill_id: str = field(default_factory=lambda: generate_id("BILL"))
    created_at: datetime = field(default_factory=datetime.now)
    price_type: str = field(init=False)
    unit_price: float = field(init=False)
    charge_fee: float = field(init=False)
    service_fee: float = field(init=False)
    total_fee: float = field(init=False)

    def __post_init__(self):
        """按充电过程分段计入峰平谷电费，服务费按电量固定收取。"""
        if self.pile_power and self.start_time and self.end_time and self.end_time > self.start_time:
            self.charge_fee, self.service_fee, self.total_fee = Bill._compute_integrated_fees(
                self.start_time,
                self.end_time,
                self.pile_power,
                self.energy_amount,
            )
        else:
            self.charge_fee, self.service_fee, self.total_fee = Bill._compute_segmented_fees(
                self.start_time,
                self.end_time,
                self.energy_amount,
            )
        self.price_type, self.unit_price = self._price_for_time(self.end_time)
        if self.energy_amount > 0:
            self.unit_price = round(self.charge_fee / self.energy_amount, 3)

    @staticmethod
    def _price_for_time(at_time: datetime):
        """需求书中的峰平谷时段规则。"""
        hour = at_time.hour
        if 10 <= hour < 15 or 18 <= hour < 21:
            return "PEAK", PEAK_PRICE
        if 7 <= hour < 10 or 15 <= hour < 18 or 21 <= hour < 23:
            return "NORMAL", NORMAL_PRICE
        return "VALLEY", VALLEY_PRICE

    @staticmethod
    def _next_price_boundary(at_time: datetime) -> datetime:
        for hour in _PRICE_BOUNDARY_HOURS:
            boundary = at_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            if boundary > at_time:
                return boundary
        next_day = at_time + timedelta(days=1)
        return next_day.replace(hour=7, minute=0, second=0, microsecond=0)

    @staticmethod
    def running_fee_for_charging(
        start_time: datetime | None,
        snapshot_time: datetime,
        pile_power: float,
        target_amount: float,
    ) -> float:
        """验收快照：按各时段实际充电量分段计费（7:00 前谷时，7:00 后平时等）。"""
        charge_fee, service_fee, total_fee = Bill._compute_integrated_fees(
            start_time,
            snapshot_time,
            pile_power,
            target_amount,
        )
        return total_fee if charge_fee or service_fee else 0.0

    @staticmethod
    def _compute_integrated_fees(
        start_time: datetime | None,
        end_time: datetime | None,
        pile_power: float,
        target_amount: float,
    ) -> tuple[float, float, float]:
        """按恒定功率充电，将各时段内充入电量乘以对应峰平谷电价。"""
        if not start_time or not end_time or end_time <= start_time or pile_power <= 0 or target_amount <= 0:
            return 0.0, 0.0, 0.0

        charge_fee = 0.0
        total_energy = 0.0
        cursor = start_time
        while cursor < end_time and total_energy < target_amount:
            _, unit_price = Bill._price_for_time(cursor)
            boundary = Bill._next_price_boundary(cursor)
            segment_end = min(end_time, boundary)
            hours = (segment_end - cursor).total_seconds() / 3600
            segment_energy = min(hours * pile_power, target_amount - total_energy)
            charge_fee += segment_energy * unit_price
            total_energy += segment_energy
            cursor = segment_end

        charge_fee = round(charge_fee, 2)
        service_fee = round(total_energy * SERVICE_FEE_RATE, 2)
        return charge_fee, service_fee, round(charge_fee + service_fee, 2)

    @staticmethod
    def running_fee_at(energy_amount: float, at_time: datetime) -> float:
        """按单一时刻电价估算（仅作兜底）。"""
        if energy_amount <= 0:
            return 0.0
        _, unit_price = Bill._price_for_time(at_time)
        charge_fee = round(energy_amount * unit_price, 2)
        service_fee = round(energy_amount * SERVICE_FEE_RATE, 2)
        return round(charge_fee + service_fee, 2)

    @staticmethod
    def _compute_segmented_fees(
        start_time: datetime | None,
        end_time: datetime | None,
        energy_amount: float,
    ) -> tuple[float, float, float]:
        """详单结算：按各时段在充电区间内的时长比例分摊电量并计费。"""
        if (
            energy_amount <= 0
            or not start_time
            or not end_time
            or end_time <= start_time
        ):
            at_time = end_time or start_time or datetime.now()
            return Bill._fees_at_single_rate(energy_amount, at_time)

        total_seconds = (end_time - start_time).total_seconds()
        charge_fee = 0.0
        cursor = start_time
        while cursor < end_time:
            _, unit_price = Bill._price_for_time(cursor)
            boundary = Bill._next_price_boundary(cursor)
            segment_end = min(end_time, boundary)
            segment_ratio = (segment_end - cursor).total_seconds() / total_seconds
            segment_energy = energy_amount * segment_ratio
            charge_fee += segment_energy * unit_price
            cursor = segment_end

        charge_fee = round(charge_fee, 2)
        service_fee = round(energy_amount * SERVICE_FEE_RATE, 2)
        return charge_fee, service_fee, round(charge_fee + service_fee, 2)

    @staticmethod
    def _fees_at_single_rate(energy_amount: float, at_time: datetime) -> tuple[float, float, float]:
        _, unit_price = Bill._price_for_time(at_time)
        charge_fee = round(energy_amount * unit_price, 2)
        service_fee = round(energy_amount * SERVICE_FEE_RATE, 2)
        return charge_fee, service_fee, round(charge_fee + service_fee, 2)

    def duration_hours(self) -> float:
        return max(0.0, (self.end_time - self.start_time).total_seconds() / 3600)

    def to_dict(self):
        return {
            "billId": self.bill_id,
            "recordId": self.bill_id,
            "sessionId": self.session_id,
            "userId": self.user_id,
            "pileId": self.pile_id,
            "energyAmount": round(self.energy_amount, 2),
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat(),
            "durationHours": round(self.duration_hours(), 3),
            "priceType": self.price_type,
            "unitPrice": self.unit_price,
            "chargeFee": self.charge_fee,
            "serviceFee": self.service_fee,
            "totalFee": self.total_fee,
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
        }

