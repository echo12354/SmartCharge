"""Fault record model."""

from dataclasses import dataclass, field
from datetime import datetime

from utils.id_generator import generate_id


@dataclass
class FaultRecord:
    pile_id: str
    reason: str
    affected_car_ids: list[str]
    fault_id: str = field(default_factory=lambda: generate_id("FAULT"))
    status: str = "FAULT"
    fault_time: datetime = field(default_factory=datetime.now)
    recovery_time: datetime | None = None

    def recover(self):
        self.status = "RECOVERED"
        self.recovery_time = datetime.now()

    def to_dict(self):
        return {
            "faultId": self.fault_id,
            "pileId": self.pile_id,
            "reason": self.reason,
            "affectedCarIds": self.affected_car_ids,
            "status": self.status,
            "faultTime": self.fault_time.isoformat(),
            "recoveryTime": self.recovery_time.isoformat() if self.recovery_time else None,
        }

