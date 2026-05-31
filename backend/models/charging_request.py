"""Charging request model."""

from dataclasses import dataclass, field
from datetime import datetime

from utils.id_generator import generate_id


@dataclass
class ChargingRequest:
    user_id: str
    charge_mode: str
    requested_amount: float
    request_id: str = field(default_factory=lambda: generate_id("REQ"))
    status: str = "WAITING"
    queue_number: str = ""
    assigned_pile_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def change_amount(self, amount: float):
        self.requested_amount = amount
        self.updated_at = datetime.now()

    def change_mode(self, mode: str):
        self.charge_mode = mode
        self.updated_at = datetime.now()

    def assign_queue_number(self, queue_number: str):
        self.queue_number = queue_number
        self.updated_at = datetime.now()

    def assign_pile(self, pile_id: str):
        self.assigned_pile_id = pile_id
        self.status = "DISPATCHED"
        self.updated_at = datetime.now()

    def mark_charging(self):
        self.status = "CHARGING"
        self.updated_at = datetime.now()

    def mark_completed(self):
        self.status = "COMPLETED"
        self.updated_at = datetime.now()

    def cancel(self):
        self.status = "CANCELLED"
        self.updated_at = datetime.now()

    def to_dict(self):
        return {
            "requestId": self.request_id,
            "userId": self.user_id,
            "chargeMode": self.charge_mode,
            "requestedAmount": self.requested_amount,
            "status": self.status,
            "queueNumber": self.queue_number,
            "assignedPileId": self.assigned_pile_id,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }

