"""验收测试用模拟时钟。

比例尺 1:10：验收表 30 分钟实操对应 300 分钟模拟时间（6:00→11:00）。
自动测试时按事件表绝对时刻推进；监控/手动操作时按真实时间 × 比例尺连续推进。
"""

from datetime import datetime, timedelta

from config.settings import (
    SIMULATION_ENABLED,
    SIMULATION_MINUTES_PER_EVENT,
    SIMULATION_START_TIME,
    SIMULATION_TIME_SCALE,
)


class SimulationClock:
    def __init__(self):
        self.enabled = SIMULATION_ENABLED
        self._current = SIMULATION_START_TIME
        self._realtime_tick = False
        self._anchor_real: datetime | None = None
        self._anchor_sim: datetime | None = None

    def now(self) -> datetime:
        if not self.enabled:
            return datetime.now()
        if self._realtime_tick and self._anchor_real and self._anchor_sim:
            real_elapsed = datetime.now() - self._anchor_real
            sim_elapsed = timedelta(seconds=real_elapsed.total_seconds() * SIMULATION_TIME_SCALE)
            return self._anchor_sim + sim_elapsed
        return self._current

    def is_enabled(self) -> bool:
        return self.enabled

    def is_realtime_tick(self) -> bool:
        return self._realtime_tick

    def enable(self, realtime_tick: bool = True):
        self.enabled = True
        if realtime_tick:
            self.enable_realtime_tick()

    def disable(self):
        self.enabled = False
        self._realtime_tick = False
        self._anchor_real = None
        self._anchor_sim = None

    def reset(self, start_time: datetime | None = None):
        self._current = start_time or SIMULATION_START_TIME
        if self._realtime_tick:
            self._anchor_sim = self._current
            self._anchor_real = datetime.now()

    def set_time(self, target: datetime):
        self._current = target
        if self._realtime_tick:
            self._anchor_sim = self._current
            self._anchor_real = datetime.now()

    def enable_realtime_tick(self):
        """按真实时间 × 比例尺推进模拟时钟，供监控页与手动操作使用。"""
        self._realtime_tick = True
        self._anchor_sim = self.now()
        self._anchor_real = datetime.now()

    def disable_realtime_tick(self):
        """冻结模拟时刻，供验收事件逐步/批量跳转使用。"""
        if self._realtime_tick:
            self._current = self.now()
        self._realtime_tick = False
        self._anchor_real = None
        self._anchor_sim = None

    def advance_minutes(self, minutes: float):
        self.set_time(self.now() + timedelta(minutes=minutes))

    def set_time_from_clock(self, hour: int, minute: int = 0):
        base = SIMULATION_START_TIME
        self.set_time(base.replace(hour=hour, minute=minute, second=0, microsecond=0))

    def to_dict(self):
        current = self.now()
        return {
            "enabled": self.enabled,
            "realtimeTick": self._realtime_tick,
            "currentTime": current.isoformat(),
            "displayTime": current.strftime("%H:%M"),
            "startTime": SIMULATION_START_TIME.isoformat(),
            "minutesPerEvent": SIMULATION_MINUTES_PER_EVENT,
            "timeScale": SIMULATION_TIME_SCALE,
        }


sim_clock = SimulationClock()
