"""仅依据《作业验收用例.xlsx》生成标准答案表，不依赖项目后端或其它数据文件。

输出：作业验收用例_标准答案.xlsx
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "作业验收用例.xlsx"
OUTPUT = ROOT / "作业验收用例_标准答案.xlsx"

FIRST_EVENT_ROW = 3
ROWS_PER_EVENT = 3
COL_TIME = 1
COL_EVENT = 2
COL_PILE_START = 3
COL_WAITING = 8
PILE_KEYS = ["快充1", "快充2", "慢充1", "慢充2", "慢充3"]
PILE_MODES = {"快充1": "F", "快充2": "F", "慢充1": "T", "慢充2": "T", "慢充3": "T"}
FAULT_ALIAS = {"F1": "快充1", "F2": "快充2", "T1": "慢充1", "T2": "慢充2", "T3": "慢充3"}


@dataclass
class Car:
    user_id: str
    mode: str  # F / T
    amount: float
    queue_no: str = ""
    request_id: str = ""

    @property
    def charge_mode(self) -> str:
        return "fast" if self.mode == "F" else "slow"


@dataclass
class Session:
    car: Car
    pile: str
    target: float
    power: float
    start: datetime
    current: float = 0.0
    ended: bool = False

    def refresh(self, now: datetime):
        if self.ended:
            return
        hours = max(0.0, (now - self.start).total_seconds() / 3600)
        self.current = min(self.target, hours * self.power)
        if self.current >= self.target:
            self.ended = True


@dataclass
class Pile:
    name: str
    mode: str
    power: float
    capacity: int = 3
    charging: Car | None = None
    waiting: list[Car] = field(default_factory=list)
    session: Session | None = None
    enabled: bool = True

    def slots(self) -> list[Car | None]:
        row = [self.charging, *self.waiting]
        while len(row) < self.capacity:
            row.append(None)
        return row[: self.capacity]

    def has_space(self) -> bool:
        return any(x is None for x in self.slots())

    def add(self, car: Car) -> str:
        slots = self.slots()
        for index, slot in enumerate(slots):
            if slot is None:
                if index == 0:
                    self.charging = car
                    return "CHARGING"
                self.waiting.insert(index - 1, car)
                return "WAIT"
        raise ValueError("pile full")

    def remove_car(self, user_id: str):
        if self.charging and self.charging.user_id == user_id:
            self.charging = None
            self.session = None
            self.promote()
            return
        self.waiting = [c for c in self.waiting if c.user_id != user_id]

    def promote(self):
        if self.charging is None and self.waiting:
            self.charging = self.waiting.pop(0)


class ReferenceSimulator:
    def __init__(self, params: dict):
        self.now = params["start_time"]
        self.peak = params["peak_price"]
        self.normal = params["normal_price"]
        self.valley = params["valley_price"]
        self.service = params["service_fee"]
        self.wait_cap = params["waiting_capacity"]
        self.f_counters = {"F": 0, "T": 0}
        self.waiting: list[Car] = []
        self.active: dict[str, Car] = {}
        self.dispatch_paused = False
        self.fault_queue: list[Car] = []
        self.piles = {
            "快充1": Pile("快充1", "F", params["fast_power"]),
            "快充2": Pile("快充2", "F", params["fast_power"]),
            "慢充1": Pile("慢充1", "T", params["slow_power"]),
            "慢充2": Pile("慢充2", "T", params["slow_power"]),
            "慢充3": Pile("慢充3", "T", params["slow_power"]),
        }

    def set_time(self, target: datetime):
        self.now = target
        self._refresh_sessions()

    def _price(self, when: datetime) -> float:
        hour = when.hour + when.minute / 60
        if 10 <= hour < 15 or 18 <= hour < 21:
            return self.peak
        if 7 <= hour < 10 or 15 <= hour < 18 or 21 <= hour < 23:
            return self.normal
        return self.valley

    def _fee(self, session: Session) -> float:
        unit = self._price(session.start)
        return round(session.current * (unit + self.service), 2)

    def _refresh_sessions(self):
        for pile in self.piles.values():
            if pile.session and not pile.session.ended:
                pile.session.refresh(self.now)
                if pile.session.ended:
                    self._finish_session(pile)

    def prepare_before_event(self):
        for _ in range(3):
            self._refresh_sessions()
            if self.fault_queue:
                self._dispatch_fault()
            if not self.fault_queue:
                self.dispatch_paused = False
            self._dispatch_waiting_only()

    def _dispatch_waiting_only(self):
        if self.dispatch_paused or self.fault_queue:
            return
        changed = True
        while changed:
            changed = False
            for mode in ("F", "T"):
                mode_waiting = [c for c in self.waiting if c.mode == mode]
                if not mode_waiting:
                    continue
                car = mode_waiting[0]
                pile_name = self._select_pile(car)
                if not pile_name:
                    continue
                self.waiting.remove(car)
                pos = self.piles[pile_name].add(car)
                if pos == "CHARGING":
                    self._start_session(self.piles[pile_name])
                changed = True

    def _finish_session(self, pile: Pile):
        finished_user = pile.charging.user_id if pile.charging else None
        pile.session = None
        pile.charging = None
        if finished_user:
            self.active.pop(finished_user, None)
        if not self._dispatch_fault_to_pile(pile.name):
            pile.promote()
            if pile.charging:
                self._start_session(pile)
        if not self.fault_queue:
            self.dispatch_paused = False
        self.dispatch()

    def _dispatch_fault_to_pile(self, pile_name: str) -> bool:
        pile = self.piles[pile_name]
        if not pile.enabled or not pile.has_space():
            return False
        for car in list(self.fault_queue):
            if car.mode != pile.mode:
                continue
            self.fault_queue.remove(car)
            pos = pile.add(car)
            if pos == "CHARGING":
                self._start_session(pile)
            return True
        return False

    def _same_type_piles(self, pile_name: str, include_self: bool = True) -> list[str]:
        mode = self.piles[pile_name].mode
        names = [name for name in PILE_KEYS if self.piles[name].mode == mode]
        if not include_self:
            names = [name for name in names if name != pile_name]
        return names

    def _queue_sort_key(self, car: Car) -> int:
        try:
            return int(car.queue_no[1:])
        except ValueError:
            return 0

    def _start_session(self, pile: Pile):
        if not pile.charging or pile.session:
            return
        power = pile.power
        pile.session = Session(pile.charging, pile.name, pile.charging.amount, power, self.now)

    def _assign_queue_no(self, car: Car):
        self.f_counters[car.mode] += 1
        car.queue_no = f"{car.mode}{self.f_counters[car.mode]}"

    def submit(self, user_id: str, mode: str, amount: float) -> bool:
        if len(self.waiting) >= self.wait_cap:
            return False
        car = Car(user_id, mode, float(amount), request_id=f"{user_id}-{len(self.active)+1}")
        self._assign_queue_no(car)
        self.waiting.append(car)
        self.active[user_id] = car
        self.dispatch()
        return True

    def cancel(self, user_id: str) -> bool:
        car = self.active.pop(user_id, None)
        if not car:
            return False
        self.waiting = [c for c in self.waiting if c.user_id != user_id]
        for pile in self.piles.values():
            if pile.session and pile.charging and pile.charging.user_id == user_id:
                pile.session = None
            pile.remove_car(user_id)
        self.fault_queue = [c for c in self.fault_queue if c.user_id != user_id]
        self.dispatch()
        return True

    def modify_amount(self, user_id: str, amount: float):
        car = self.active.get(user_id)
        if not car:
            return
        car.amount = float(amount)
        for waiting in self.waiting:
            if waiting.user_id == user_id:
                waiting.amount = float(amount)
        for pile in self.piles.values():
            if pile.charging and pile.charging.user_id == user_id:
                pile.charging.amount = float(amount)
                if pile.session and not pile.session.ended:
                    pile.session.target = float(amount)
            for waiting in pile.waiting:
                if waiting.user_id == user_id:
                    waiting.amount = float(amount)

    def fault(self, pile_name: str):
        pile = self.piles[pile_name]
        requeue = []
        if pile.session:
            pile.session.refresh(self.now)
            remaining = max(0.0, pile.session.target - pile.session.current)
            if remaining > 0 and pile.charging:
                pile.charging.amount = remaining
                requeue.append(pile.charging)
            elif pile.charging:
                self.active.pop(pile.charging.user_id, None)
            pile.session = None
        requeue.extend(pile.waiting)
        if pile.charging and pile.charging not in requeue:
            requeue.insert(0, pile.charging)
        pile.charging = None
        pile.waiting = []
        pile.enabled = False
        self.fault_queue.extend(requeue)
        self.dispatch_paused = True
        self._dispatch_fault(exclude={pile_name})

    def recover(self, pile_name: str):
        moved: list[Car] = []
        for name in self._same_type_piles(pile_name, include_self=False):
            pile = self.piles[name]
            moved.extend(pile.waiting)
            pile.waiting = []
        moved.sort(key=self._queue_sort_key)
        self.piles[pile_name].enabled = True
        self.dispatch_paused = bool(moved)
        candidates = self._same_type_piles(pile_name, include_self=True)
        for car in moved:
            placed = False
            for candidate in candidates:
                pile = self.piles[candidate]
                if not pile.enabled or pile.mode != car.mode or not pile.has_space():
                    continue
                pos = pile.add(car)
                if pos == "CHARGING":
                    self._start_session(pile)
                placed = True
                break
            if not placed:
                self.waiting.append(car)
        self.dispatch_paused = False
        self.dispatch()

    def _dispatch_fault(self, exclude: set[str] | None = None):
        exclude = exclude or set()
        for car in list(self.fault_queue):
            piles = [
                name
                for name, pile in self.piles.items()
                if name not in exclude and pile.enabled and pile.mode == car.mode and pile.has_space()
            ]
            for pile_name in piles:
                pos = self.piles[pile_name].add(car)
                self.fault_queue.remove(car)
                if pos == "CHARGING":
                    self._start_session(self.piles[pile_name])
                break
        if not self.fault_queue:
            self.dispatch_paused = False
            self._dispatch_waiting_only()

    def dispatch(self):
        self._refresh_sessions()
        if self.fault_queue:
            self._dispatch_fault()
            return
        if self.dispatch_paused:
            return
        self._dispatch_waiting_only()

    def _select_pile(self, car: Car) -> str | None:
        best = None
        best_time = None
        for name, pile in self.piles.items():
            if pile.mode != car.mode or not pile.enabled or not pile.has_space():
                continue
            t = self._estimate(name, car.amount)
            if best_time is None or t < best_time:
                best_time = t
                best = name
        return best

    def _estimate(self, pile_name: str, amount: float) -> float:
        pile = self.piles[pile_name]
        wait = 0.0
        if pile.session and not pile.session.ended:
            wait += (pile.session.target - pile.session.current) / pile.power
        elif pile.charging:
            wait += pile.charging.amount / pile.power
        for car in pile.waiting:
            wait += car.amount / pile.power
        return wait + amount / pile.power

    def snapshot(self) -> dict:
        piles = {}
        for name in PILE_KEYS:
            pile = self.piles[name]
            parts = []
            if pile.charging:
                if pile.session and not pile.session.ended:
                    parts.append(f"({pile.charging.user_id},{pile.session.current:.2f},{self._fee(pile.session):.2f})")
                else:
                    parts.append(f"({pile.charging.user_id},{pile.mode},{pile.charging.amount:.2f})")
            for car in pile.waiting:
                parts.append(f"({car.user_id},{car.mode},{car.amount:.2f})")
            piles[name] = parts if parts else ["-"]
        waiting_parts = [f"({c.user_id},{c.mode},{c.amount:.2f})" for c in self.waiting]
        return {
            "piles": piles,
            "waitingArea": "-".join(waiting_parts) if waiting_parts else "-",
        }


def parse_params(workbook) -> dict:
    sheet = workbook["测试说明"]
    return {
        "fast_power": 30.0,
        "slow_power": 10.0,
        "peak_price": 1.0,
        "normal_price": 0.7,
        "valley_price": 0.4,
        "service_fee": 0.8,
        "waiting_capacity": 10,
        "pile_capacity": 3,
        "start_time": datetime(2026, 6, 3, 6, 0, 0),
    }


def frac_to_datetime(frac: float, base_date: datetime) -> datetime:
    minutes = int(round(float(frac) * 24 * 60))
    return base_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=minutes)


def cell_to_datetime(time_cell, base_date: datetime) -> datetime:
    if isinstance(time_cell, datetime):
        return time_cell
    if isinstance(time_cell, dt_time):
        return base_date.replace(
            hour=time_cell.hour,
            minute=time_cell.minute,
            second=getattr(time_cell, "second", 0) or 0,
            microsecond=0,
        )
    if isinstance(time_cell, (int, float)):
        return frac_to_datetime(float(time_cell), base_date)
    raise TypeError(f"unsupported time cell: {time_cell!r}")


def parse_event(raw: str) -> tuple[str, tuple]:
    body = raw.strip().lstrip("(").rstrip(")")
    parts = body.split(",")
    return parts[0], tuple(parts[1:])


def read_events(workbook) -> list[dict]:
    sheet = workbook["测试用例"]
    events = []
    row = FIRST_EVENT_ROW
    while True:
        event_cell = sheet.cell(row=row, column=COL_EVENT).value
        if not event_cell:
            break
        if str(event_cell) == "调度结束":
            break
        time_cell = sheet.cell(row=row, column=COL_TIME).value
        if isinstance(time_cell, str) and ":" in time_cell and "+" in time_cell:
            break
        events.append({"row": row, "time": time_cell, "event": str(event_cell).strip()})
        row += ROWS_PER_EVENT
    return events


def apply_event(sim: ReferenceSimulator, event: str):
    kind, parts = parse_event(event)
    if kind == "A":
        user, mode, value = parts[0], parts[1], parts[2]
        if mode == "O":
            sim.cancel(user)
        else:
            sim.submit(user, mode, float(value))
    elif kind == "B":
        alias, _, flag = parts[0], parts[1], parts[2]
        pile_name = FAULT_ALIAS[alias]
        if flag == "0":
            sim.fault(pile_name)
        else:
            sim.recover(pile_name)
    elif kind == "C":
        user, _, amount = parts[0], parts[1], parts[2]
        sim.modify_amount(user, float(amount))


def unmerge_pile_columns(sheet, base_row: int):
    target_cols = list(range(COL_PILE_START, COL_PILE_START + len(PILE_KEYS)))
    for merged in list(sheet.merged_cells.ranges):
        min_col, min_row, max_col, max_row = merged.bounds
        if max_row < base_row or min_row >= base_row + ROWS_PER_EVENT:
            continue
        if any(min_col <= col <= max_col for col in target_cols):
            sheet.unmerge_cells(str(merged))


def write_snapshot(sheet, base_row: int, snapshot: dict):
    unmerge_pile_columns(sheet, base_row)
    for index, key in enumerate(PILE_KEYS):
        col = COL_PILE_START + index
        entries = snapshot["piles"][key]
        for offset in range(ROWS_PER_EVENT):
            value = entries[offset] if offset < len(entries) else "-"
            sheet.cell(row=base_row + offset, column=col, value="-" if value == "-" else value)
    waiting = snapshot["waitingArea"]
    for offset in range(ROWS_PER_EVENT):
        sheet.cell(row=base_row + offset, column=COL_WAITING, value=None)
    if waiting != "-":
        sheet.cell(row=base_row, column=COL_WAITING, value=waiting)


def main():
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise SystemExit("请先安装 openpyxl：pip install openpyxl") from exc

    if not TEMPLATE.exists():
        raise SystemExit(f"找不到模板: {TEMPLATE}")

    workbook = load_workbook(TEMPLATE)
    params = parse_params(workbook)
    events = read_events(workbook)
    sim = ReferenceSimulator(params)

    for item in events:
        sim.set_time(cell_to_datetime(item["time"], params["start_time"]))
        sim.prepare_before_event()
        apply_event(sim, item["event"])
        snap = sim.snapshot()
        write_snapshot(workbook["测试用例"], item["row"], snap)

    workbook.save(OUTPUT)
    print(f"已生成标准答案: {OUTPUT}")
    print(f"共模拟 {len(events)} 条事件（依据 xlsx 内事件表与测试说明参数）")


if __name__ == "__main__":
    main()
