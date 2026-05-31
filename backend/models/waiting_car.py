"""Waiting car model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WaitingCar:
    user_id: str
    request_id: str
    charge_mode: str
    requested_amount: float
    queue_number: str = ""
    queue_position: str = "WAITING_AREA"
    assigned_pile_id: str | None = None
    join_time: datetime = field(default_factory=datetime.now)

    def waiting_minutes(self) -> int:
        return int((datetime.now() - self.join_time).total_seconds() // 60)

    def to_dict(self):
        return {
            "userId": self.user_id,
            "requestId": self.request_id,
            "chargeMode": self.charge_mode,
            "requestedAmount": self.requested_amount,
            "queueNumber": self.queue_number,
            "queuePosition": self.queue_position,
            "assignedPileId": self.assigned_pile_id,
            "joinTime": self.join_time.isoformat(),
            "queueTime": f"{self.waiting_minutes()}分钟",
        }

