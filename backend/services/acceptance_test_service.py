"""作业验收用例自动测试服务。

按《作业验收用例.xlsx》推进模拟时钟、执行事件并生成与表格一致的快照。
"""

from __future__ import annotations

from datetime import datetime

from config.settings import (
    ACCEPTANCE_FAST_PILE_ALIAS,
    ACCEPTANCE_SLOW_PILE_ALIAS,
    FAST_PILES,
    SIMULATION_START_TIME,
    SLOW_PILES,
)
from models.bill import Bill
from models.pile_queue import PileQueue
from models.waiting_queue import WaitingQueue
from services.charging_session_service import charging_session_service
from services.fault_recovery_service import fault_recovery_service
from services.pile_management_service import pile_management_service
from services.queue_service import queue_service
from services.scheduling_service import scheduling_service
from services.user_service import user_service
from utils.sim_clock import sim_clock

PILE_COLUMNS = [
    ("A", "快充1"),
    ("B", "快充2"),
    ("C", "慢充1"),
    ("D", "慢充2"),
    ("E", "慢充3"),
]

# 作业验收用例.xlsx「测试用例」sheet 中的 42 条事件（模拟时刻 HH:MM）。
ACCEPTANCE_EVENTS: list[tuple[str, tuple[str, ...]]] = [
    ("06:00", ("A", "V1", "T", "40")),
    ("06:05", ("A", "V2", "T", "30")),
    ("06:10", ("A", "V3", "F", "100")),
    ("06:15", ("A", "V4", "F", "120")),
    ("06:20", ("A", "V2", "O", "0")),
    ("06:25", ("A", "V5", "T", "20")),
    ("06:30", ("A", "V6", "T", "20")),
    ("06:35", ("A", "V7", "F", "110")),
    ("06:40", ("A", "V8", "T", "20")),
    ("06:45", ("A", "V9", "F", "105")),
    ("06:50", ("A", "V10", "T", "10")),
    ("06:55", ("A", "V11", "F", "110")),
    ("07:00", ("A", "V12", "F", "90")),
    ("07:05", ("A", "V13", "F", "110")),
    ("07:10", ("A", "V14", "F", "95")),
    ("07:15", ("A", "V15", "T", "10")),
    ("07:20", ("A", "V16", "F", "60")),
    ("07:25", ("A", "V17", "T", "10")),
    ("07:30", ("A", "V18", "T", "7.5")),
    ("07:35", ("A", "V19", "F", "75")),
    ("07:40", ("A", "V20", "F", "95")),
    ("07:45", ("A", "V21", "F", "95")),
    ("07:50", ("A", "V22", "F", "70")),
    ("07:55", ("A", "V23", "F", "80")),
    ("08:00", ("A", "V24", "T", "5")),
    ("08:20", ("A", "V25", "T", "15")),
    ("08:25", ("B", "T1", "O", "0")),
    ("08:30", ("A", "V26", "T", "20")),
    ("08:35", ("A", "V27", "T", "25")),
    ("08:50", ("B", "F1", "O", "0")),
    ("09:00", ("A", "V28", "F", "30")),
    ("09:10", ("A", "V1", "O", "0")),
    ("09:15", ("B", "T1", "O", "1")),
    ("09:20", ("A", "V27", "O", "0")),
    ("09:25", ("C", "V21", "O", "35")),
    ("09:30", ("A", "V19", "O", "0")),
    ("09:35", ("A", "V28", "O", "0")),
    ("09:40", ("C", "V23", "O", "40")),
    ("09:50", ("A", "V29", "T", "30")),
    ("09:55", ("C", "V14", "O", "30")),
    ("10:00", ("A", "V30", "T", "10")),
    ("10:50", ("B", "F1", "O", "1")),
]


class AcceptanceTestService:
    def __init__(self):
        self._request_ids: dict[str, str] = {}
        self._failed_submit_vehicles: set[str] = set()
        self._last_event_index = 0

    def reset(self):
        """重置为验收初始状态并启用模拟时钟。"""
        sim_clock.enable(realtime_tick=False)
        sim_clock.reset(SIMULATION_START_TIME)
        sim_clock.enable_realtime_tick()
        self._request_ids = {}
        self._failed_submit_vehicles = set()
        self._last_event_index = 0

        queue_service.waiting_queue = WaitingQueue()
        queue_service.requests_by_id = {}
        queue_service.active_requests_by_user = {}
        scheduling_service.pile_queues = {pile_id: PileQueue(pile_id) for pile_id in (*FAST_PILES, *SLOW_PILES)}
        scheduling_service.decisions = []
        scheduling_service.fault_priority_queue = []
        scheduling_service.dispatch_paused = False
        scheduling_service.engine_running = True

        charging_session_service.active_sessions = {}
        charging_session_service.completed_sessions = {}
        charging_session_service.user_active_sessions = {}
        charging_session_service.request_active_session = {}
        charging_session_service.pile_active_session = {}

        for pile in pile_management_service.list_piles():
            pile.power_on()
            pile.current_session_id = None
            pile.status = "ACTIVE"

        for index in range(1, 31):
            username = f"V{index}"
            if not user_service.get_user(username):
                user_service.register(username, "123", "user")

        return {"message": "acceptance environment reset", "clock": sim_clock.to_dict()}

    def run_all(self, stop_at: str = "09:30", strategy: str = "priority"):
        """连续执行事件直到达到指定模拟时刻。"""
        self.reset()
        sim_clock.disable_realtime_tick()
        results = []
        stop_minutes = self._clock_to_minutes(stop_at)
        for index, (clock, event) in enumerate(ACCEPTANCE_EVENTS, start=1):
            event_minutes = self._clock_to_minutes(clock)
            if event_minutes > stop_minutes:
                break
            results.append(self._run_event_body(index, strategy=strategy))
        sim_clock.enable_realtime_tick()
        return {
            "executed": len(results),
            "stopAt": stop_at,
            "results": results,
            "finalSnapshot": self.get_snapshot(),
        }

    def run_event(self, event_index: int, strategy: str = "priority"):
        if event_index < 1 or event_index > len(ACCEPTANCE_EVENTS):
            raise ValueError("event index out of range")
        sim_clock.disable_realtime_tick()
        result = self._run_event_body(event_index, strategy=strategy)
        sim_clock.enable_realtime_tick()
        return result

    def _run_event_body(self, event_index: int, strategy: str = "priority", include_snapshot: bool = True):
        clock, event = ACCEPTANCE_EVENTS[event_index - 1]
        self._advance_to_clock(clock)
        self._prepare_dispatch_before_event()
        action = self._execute_event(event, strategy=strategy)
        charging_session_service.refresh_all_active_sessions()
        scheduling_service.refresh_finished_sessions()
        self._last_event_index = event_index
        result = {
            "index": event_index,
            "simTime": clock,
            "event": self._format_event(event),
            "action": action,
        }
        if include_snapshot:
            result["snapshot"] = self.get_snapshot(strategy=strategy)
        return result

    def run_next(self, strategy: str = "priority"):
        next_index = self._last_event_index + 1
        if next_index > len(ACCEPTANCE_EVENTS):
            raise ValueError("all acceptance events have been executed")
        return self.run_event(next_index, strategy=strategy)

    def get_snapshot(self, strategy: str = "priority"):
        self._run_due_events(strategy=strategy)
        scheduling_service.system_tick()
        snapshot_time = self._snapshot_time()
        piles = {label: self._format_pile_column(pile_id, snapshot_time) for pile_id, label in PILE_COLUMNS}
        return {
            "simTime": snapshot_time.strftime("%H:%M"),
            "clock": sim_clock.to_dict(),
            "piles": piles,
            "waitingArea": self._format_waiting_area(),
            "lastEventIndex": self._last_event_index,
        }

    def _run_due_events(self, strategy: str = "priority"):
        if not sim_clock.is_enabled() or not sim_clock.is_realtime_tick():
            return []

        current_time = sim_clock.now()
        current_minutes = current_time.hour * 60 + current_time.minute
        due_results = []
        sim_clock.disable_realtime_tick()
        try:
            while self._last_event_index < len(ACCEPTANCE_EVENTS):
                next_index = self._last_event_index + 1
                clock, _event = ACCEPTANCE_EVENTS[next_index - 1]
                if self._clock_to_minutes(clock) > current_minutes:
                    break
                due_results.append(self._run_event_body(next_index, strategy=strategy, include_snapshot=False))
            sim_clock.set_time(current_time)
        finally:
            sim_clock.enable_realtime_tick()
        return due_results

    def _advance_to_clock(self, clock: str):
        hour, minute = [int(part) for part in clock.split(":")]
        target = SIMULATION_START_TIME.replace(hour=hour, minute=minute, second=0, microsecond=0)
        sim_clock.set_time(target)

    @staticmethod
    def _clock_to_minutes(clock: str) -> int:
        hour, minute = [int(part) for part in clock.split(":")]
        return hour * 60 + minute

    def _execute_event(self, event: tuple[str, ...], strategy: str = "priority"):
        kind = event[0]
        if kind == "A":
            return self._handle_arrival_or_cancel(event)
        if kind == "B":
            return self._handle_pile_fault(event, strategy=strategy)
        if kind == "C":
            return self._handle_modify_amount(event)
        raise ValueError(f"unsupported event: {event}")

    def _prepare_dispatch_before_event(self):
        """按模拟时刻刷新充电进度，并尽量解除故障调度导致的等候区积压。"""
        charging_session_service.refresh_all_active_sessions()
        scheduling_service.refresh_finished_sessions()
        for _ in range(3):
            if scheduling_service.fault_priority_queue:
                scheduling_service.dispatch_fault_priority_queue()
            if not scheduling_service.fault_priority_queue:
                scheduling_service.dispatch_paused = False
            scheduling_service.dispatch_waiting_cars()
            charging_session_service.refresh_all_active_sessions()
            scheduling_service.refresh_finished_sessions()

    def _handle_arrival_or_cancel(self, event: tuple[str, ...]):
        _, vehicle, mode, value = event
        if mode == "O":
            try:
                request_id = self._require_request_id(vehicle)
                request = queue_service.cancel_request(vehicle, request_id)
            except ValueError as exc:
                return self._skip_missing_request_event(vehicle, "cancel", exc)
            self._request_ids.pop(vehicle, None)
            self._failed_submit_vehicles.discard(vehicle)
            return {"type": "cancel", "userId": vehicle, "requestId": request.request_id}

        charge_mode = "fast" if mode == "F" else "slow"
        amount = float(value)
        try:
            request = queue_service.submit_request(vehicle, charge_mode, amount, vehicle_label=vehicle)
        except ValueError as exc:
            if "waiting queue is full" not in str(exc):
                raise
            self._failed_submit_vehicles.add(vehicle)
            return {
                "type": "submit_failed",
                "userId": vehicle,
                "chargeMode": charge_mode,
                "amount": amount,
                "reason": "waiting queue is full",
                "message": "提交失败：等候区已满",
            }
        self._request_ids[vehicle] = request.request_id
        self._failed_submit_vehicles.discard(vehicle)
        return {
            "type": "submit",
            "userId": vehicle,
            "requestId": request.request_id,
            "queueNumber": request.queue_number,
            "chargeMode": request.charge_mode,
            "amount": request.requested_amount,
        }

    def _handle_pile_fault(self, event: tuple[str, ...], strategy: str = "priority"):
        _, pile_alias, _, flag = event
        pile_id = self._resolve_pile_alias(pile_alias)
        if flag == "0":
            record, dispatched = fault_recovery_service.power_off_with_fault(pile_id, "acceptance fault", strategy)
            return {
                "type": "fault",
                "pileId": pile_id,
                "faultId": record.fault_id,
                "dispatched": [car.user_id for car in dispatched],
            }
        record, dispatched = fault_recovery_service.recover_pile(pile_id)
        return {
            "type": "recover",
            "pileId": pile_id,
            "faultId": record.fault_id if record else None,
            "dispatched": [car.user_id for car in dispatched],
        }

    def _handle_modify_amount(self, event: tuple[str, ...]):
        _, vehicle, _, amount = event
        try:
            request_id = self._require_request_id(vehicle)
            request = queue_service.modify_amount(vehicle, float(amount), request_id)
        except ValueError as exc:
            return self._skip_missing_request_event(vehicle, "modify_amount", exc)
        return {
            "type": "modify_amount",
            "userId": vehicle,
            "requestId": request.request_id,
            "amount": request.requested_amount,
        }

    def _require_request_id(self, vehicle: str) -> str:
        request_id = self._request_ids.get(vehicle)
        if request_id:
            return request_id
        for request in queue_service.list_active_requests(vehicle):
            self._request_ids[vehicle] = request.request_id
            return request.request_id
        raise ValueError(f"active request not found for {vehicle}")

    def _skip_missing_request_event(self, vehicle: str, action: str, exc: ValueError):
        reason = "previous_submit_failed" if vehicle in self._failed_submit_vehicles else "active_request_missing"
        message = (
            f"{vehicle} 此前提交失败，无需取消"
            if action == "cancel" and reason == "previous_submit_failed"
            else f"{vehicle} 无有效充电请求，已跳过该验收事件"
        )
        return {
            "type": "skipped",
            "success": False,
            "userId": vehicle,
            "action": action,
            "reason": reason,
            "message": message,
            "detail": str(exc),
        }

    @staticmethod
    def _resolve_pile_alias(alias: str) -> str:
        if alias in ACCEPTANCE_FAST_PILE_ALIAS:
            return ACCEPTANCE_FAST_PILE_ALIAS[alias]
        if alias in ACCEPTANCE_SLOW_PILE_ALIAS:
            return ACCEPTANCE_SLOW_PILE_ALIAS[alias]
        raise ValueError(f"unknown pile alias: {alias}")

    def _format_pile_column(self, pile_id: str, snapshot_time: datetime) -> str:
        queue = scheduling_service.pile_queues[pile_id]
        parts: list[str] = []
        if queue.charging_car:
            session = charging_session_service.get_request_active_session(queue.charging_car.request_id)
            if session:
                current_amount = self._current_amount_at(session, snapshot_time)
                parts.append(
                    f"({queue.charging_car.user_id},{current_amount:.2f},"
                    f"{self._running_fee(session, snapshot_time):.2f})"
                )
            else:
                mode = "F" if queue.charging_car.charge_mode == "fast" else "T"
                parts.append(f"({queue.charging_car.user_id},{mode},{queue.charging_car.requested_amount:.2f})")
        for waiting in queue.waiting_cars:
            mode = "F" if waiting.charge_mode == "fast" else "T"
            parts.append(f"({waiting.user_id},{mode},{waiting.requested_amount:.2f})")
        return "-".join(parts) if parts else "-"

    def _format_waiting_area(self) -> str:
        parts = []
        for car in queue_service.waiting_queue.cars:
            mode = "F" if car.charge_mode == "fast" else "T"
            parts.append(f"({car.user_id},{mode},{car.requested_amount:.2f})")
        return "-".join(parts) if parts else "-"

    def _snapshot_time(self) -> datetime:
        current = sim_clock.now()
        if 1 <= self._last_event_index <= len(ACCEPTANCE_EVENTS):
            clock, _event = ACCEPTANCE_EVENTS[self._last_event_index - 1]
            hour, minute = [int(part) for part in clock.split(":")]
            return SIMULATION_START_TIME.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return current.replace(second=0, microsecond=0)

    @staticmethod
    def _current_amount_at(session, snapshot_time: datetime) -> float:
        if not session.start_time:
            return 0.0
        stable_start = session.start_time.replace(second=0, microsecond=0)
        stable_end = session.end_time.replace(second=0, microsecond=0) if session.end_time else snapshot_time
        stable_time = min(snapshot_time, stable_end)
        elapsed_hours = max(0.0, (stable_time - stable_start).total_seconds() / 3600)
        return min(session.target_amount, elapsed_hours * session.pile_power)

    @staticmethod
    def _running_fee(session, snapshot_time: datetime) -> float:
        if not session.start_time:
            return 0.0
        stable_start = session.start_time.replace(second=0, microsecond=0)
        stable_end = snapshot_time.replace(second=0, microsecond=0)
        return Bill.running_fee_for_charging(
            stable_start,
            stable_end,
            session.pile_power,
            session.target_amount,
        )

    @staticmethod
    def _format_event(event: tuple[str, ...]) -> str:
        return "(" + ",".join(str(item) for item in event) + ")"


acceptance_test_service = AcceptanceTestService()
