"""Bill model."""

from dataclasses import dataclass, field
from datetime import datetime

from config.settings import NORMAL_PRICE, PEAK_PRICE, SERVICE_FEE_RATE, VALLEY_PRICE
from utils.id_generator import generate_id


@dataclass
class Bill:
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

    def __post_init__(self):
        self.price_type, self.unit_price = self._price_for_time(self.start_time)
        self.charge_fee = round(self.energy_amount * self.unit_price, 2)
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

