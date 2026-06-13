"""故障记录模型。

记录充电桩故障发生、影响车辆和恢复时间，用于故障调度过程追踪。
"""

from dataclasses import dataclass, field
from datetime import datetime

from utils.id_generator import generate_id


@dataclass
class FaultRecord:
    """一次故障处理的业务记录。

    `affected_car_ids` 保存故障发生时该桩队列中受影响的车辆用户 ID。
    """

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

