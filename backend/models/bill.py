"""Bill model."""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from config.settings import NORMAL_PRICE, PEAK_PRICE, SERVICE_FEE_RATE, VALLEY_PRICE
from utils.id_generator import generate_id


@dataclass
class Bill:
    """Charging bill generated after a charging session ends."""

    session_id: str
    user_id: str
    pile_id: str
    energy_amount: float
    start_time: datetime
    end_time: datetime
    status: str
    bill_id: str = field(default_factory=lambda: generate_id("BILL"))
    created_at: datetime = field(default_factory=datetime.now)
    price_type: str = field(init=False)
    unit_price: float = field(init=False)
    charge_fee: float = field(init=False)
    service_fee: float = field(init=False)
    total_fee: float = field(init=False)
    price_breakdown: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.price_breakdown = self._calculate_price_breakdown()
        self.charge_fee = round(sum(item["fee"] for item in self.price_breakdown), 2)
        if len(self.price_breakdown) == 1:
            self.price_type = self.price_breakdown[0]["priceType"]
            self.unit_price = self.price_breakdown[0]["unitPrice"]
        else:
            self.price_type = "MIXED"
            self.unit_price = round(self.charge_fee / self.energy_amount, 3) if self.energy_amount > 0 else 0.0
        self.service_fee = round(self.energy_amount * SERVICE_FEE_RATE, 2)
        self.total_fee = round(self.charge_fee + self.service_fee, 2)

    @staticmethod
    def _price_for_time(start_time: datetime):
        hour = start_time.hour
        if 10 <= hour < 15 or 18 <= hour < 21:
            return "PEAK", PEAK_PRICE
        if 7 <= hour < 10 or 15 <= hour < 18 or 21 <= hour < 23:
            return "NORMAL", NORMAL_PRICE
        return "VALLEY", VALLEY_PRICE

    @staticmethod
    def _next_tariff_boundary(moment: datetime):
        boundaries = [
            time(7, 0),
            time(10, 0),
            time(15, 0),
            time(18, 0),
            time(21, 0),
            time(23, 0),
        ]
        today = moment.date()
        candidates = [datetime.combine(today, item) for item in boundaries if datetime.combine(today, item) > moment]
        if candidates:
            return min(candidates)
        return datetime.combine(today + timedelta(days=1), time(7, 0))

    def _calculate_price_breakdown(self):
        duration_seconds = max(0.0, (self.end_time - self.start_time).total_seconds())
        if self.energy_amount <= 0 or duration_seconds <= 0:
            price_type, unit_price = self._price_for_time(self.start_time)
            return [{
                "priceType": price_type,
                "unitPrice": unit_price,
                "energyAmount": 0.0,
                "durationHours": 0.0,
                "fee": 0.0,
            }]

        energy_per_second = self.energy_amount / duration_seconds
        cursor = self.start_time
        breakdown = []
        while cursor < self.end_time:
            segment_end = min(self.end_time, self._next_tariff_boundary(cursor))
            segment_seconds = max(0.0, (segment_end - cursor).total_seconds())
            price_type, unit_price = self._price_for_time(cursor)
            energy = segment_seconds * energy_per_second
            breakdown.append({
                "priceType": price_type,
                "unitPrice": unit_price,
                "energyAmount": round(energy, 6),
                "durationHours": round(segment_seconds / 3600, 6),
                "fee": round(energy * unit_price, 6),
            })
            cursor = segment_end
        return breakdown

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
            "priceBreakdown": self.price_breakdown,
            "chargeFee": self.charge_fee,
            "serviceFee": self.service_fee,
            "totalFee": self.total_fee,
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
        }

