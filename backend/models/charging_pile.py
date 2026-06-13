"""充电桩模型。

表示站内一台可执行充电任务的设备，记录类型、功率、运行状态和累计统计。
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChargingPile:
    """充电桩运行状态对象。

    `pile_type` 区分快充/慢充，`power` 对应需求书中的充电功率，
    `current_session_id` 表示当前正在服务的充电会话。
    """

    pile_id: str
    pile_type: str
    power: float
    status: str = "ACTIVE"
    is_enabled: bool = True
    parameters: dict = field(default_factory=dict)
    total_sessions: int = 0
    total_energy: float = 0.0
    total_hours: float = 0.0
    current_session_id: str | None = None
    updated_at: datetime = field(default_factory=datetime.now)

    def power_on(self):
        self.is_enabled = True
        self.status = "ACTIVE"
        self.updated_at = datetime.now()

    def power_off(self):
        self.is_enabled = False
        self.status = "OFFLINE"
        self.updated_at = datetime.now()

    def start(self):
        if not self.is_enabled:
            raise ValueError("pile is not enabled")
        self.status = "ACTIVE"
        self.updated_at = datetime.now()

    def mark_charging(self, session_id: str):
        if not self.is_enabled:
            raise ValueError("pile is not enabled")
        self.current_session_id = session_id
        self.status = "CHARGING"
        self.updated_at = datetime.now()

    def mark_available(self):
        if self.is_enabled:
            self.status = "ACTIVE"
        self.current_session_id = None
        self.updated_at = datetime.now()

    def mark_fault(self):
        self.is_enabled = False
        self.status = "FAULT"
        self.updated_at = datetime.now()

    def update_parameters(self, parameters: dict):
        self.parameters.update(parameters)
        self.updated_at = datetime.now()

    def add_statistics(self, energy: float, hours: float):
        self.total_sessions += 1
        self.total_energy += energy
        self.total_hours += hours
        self.updated_at = datetime.now()

    def to_dict(self):
        return {
            "pileId": self.pile_id,
            "pileType": self.pile_type,
            "power": self.power,
            "status": self.status,
            "isEnabled": self.is_enabled,
            "parameters": self.parameters,
            "totalSessions": self.total_sessions,
            "totalEnergy": round(self.total_energy, 2),
            "totalHours": round(self.total_hours, 2),
            "currentSessionId": self.current_session_id,
            "updatedAt": self.updated_at.isoformat(),
        }

