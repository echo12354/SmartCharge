"""充电会话模型。

表示车辆真正进入充电桩后的一次充电过程，用于计算进度、时长和账单。
"""

from dataclasses import dataclass, field
from datetime import datetime

from utils.id_generator import generate_id


@dataclass
class ChargingSession:
    """一次充电过程的运行状态。

    `target_amount` 是目标电量，`current_amount` 是已充电量，
    `pile_power` 用来按时间推算实时充电进度。
    """

    user_id: str
    pile_id: str
    target_amount: float
    pile_power: float
    request_id: str | None = None
    session_id: str = field(default_factory=lambda: generate_id("SESSION"))
    status: str = "PREPARING"
    current_amount: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None
    stop_reason: str | None = None

    def start(self):
        self.status = "CHARGING"
        self.start_time = datetime.now()

    def refresh_progress(self):
        """按已运行时间和充电桩功率刷新当前电量。"""
        if self.status != "CHARGING" or not self.start_time:
            return
        elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        self.current_amount = min(self.target_amount, elapsed_hours * self.pile_power)
        if self.current_amount >= self.target_amount:
            self.complete()

    def complete(self):
        self.status = "COMPLETED"
        self.current_amount = self.target_amount
        self.end_time = datetime.now()
        self.stop_reason = "completed"

    def stop(self, reason: str = "manual stop"):
        self.refresh_progress()
        if self.status == "COMPLETED":
            return
        self.status = "INTERRUPTED"
        self.end_time = datetime.now()
        self.stop_reason = reason

    def duration_hours(self) -> float:
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return max(0.0, (end - self.start_time).total_seconds() / 3600)

    def progress_percent(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        self.refresh_progress()
        return min(100.0, self.current_amount / self.target_amount * 100)

    def remaining_hours(self) -> float:
        self.refresh_progress()
        if self.status != "CHARGING":
            return 0.0
        return max(0.0, (self.target_amount - self.current_amount) / self.pile_power)

    def to_dict(self):
        self.refresh_progress()
        return {
            "sessionId": self.session_id,
            "requestId": self.request_id,
            "userId": self.user_id,
            "pileId": self.pile_id,
            "targetAmount": self.target_amount,
            "currentAmount": round(self.current_amount, 2),
            "pilePower": self.pile_power,
            "status": self.status,
            "progressPercent": round(self.progress_percent(), 1),
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "durationHours": round(self.duration_hours(), 3),
            "remainingHours": round(self.remaining_hours(), 3),
            "stopReason": self.stop_reason,
        }

