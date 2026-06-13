"""Dispatch decision model."""

from dataclasses import dataclass, field
from datetime import datetime

from utils.id_generator import generate_id


@dataclass
class DispatchDecision:
    request_id: str
    user_id: str
    selected_pile_id: str
    strategy: str
    reason: str
    expected_completion_hours: float
    decision_id: str = field(default_factory=lambda: generate_id("DISPATCH"))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "decisionId": self.decision_id,
            "requestId": self.request_id,
            "userId": self.user_id,
            "selectedPileId": self.selected_pile_id,
            "strategy": self.strategy,
            "reason": self.reason,
            "expectedCompletionHours": round(self.expected_completion_hours, 3),
            "createdAt": self.created_at.isoformat(),
        }

