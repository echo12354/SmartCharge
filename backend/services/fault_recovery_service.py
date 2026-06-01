"""故障处理与恢复服务。

负责充电桩下电、故障恢复以及故障车辆的重新调度。
故障记录优先写入 MySQL，运行时队列仍保留在内存中。
"""

from config.settings import FAST_PILES, SLOW_PILES
from models.fault_record import FaultRecord
from models.waiting_car import WaitingCar
from repositories.fault_repository import FaultRepository
from services.charging_session_service import charging_session_service
from services.pile_management_service import pile_management_service
from services.scheduling_service import scheduling_service


class FaultRecoveryService:
    def __init__(self):
        self.records: dict[str, FaultRecord] = {}
        self.latest_fault_by_pile: dict[str, str] = {}
        self.repository = FaultRepository()
        self._load_records_from_database()

    def power_off_with_fault(self, pile_id: str, reason: str = "manual power off", strategy: str = "priority"):
        """充电桩故障/下电处理。

        当前充电车辆会先结算已充部分，未完成电量和桩前等待车辆进入重新调度流程。
        """
        pile = pile_management_service.get_pile(pile_id)
        if not pile:
            raise ValueError("pile not found")
        queue = scheduling_service.pile_queues[pile_id]
        affected = queue.cars()
        affected_ids = [car.user_id for car in affected]
        record = FaultRecord(pile_id=pile_id, reason=reason, affected_car_ids=affected_ids)
        self.records[record.fault_id] = record
        self.latest_fault_by_pile[pile_id] = record.fault_id
        self._save_record_to_database(record)

        requeue_cars: list[WaitingCar] = []
        active_session = charging_session_service.get_pile_active_session(pile_id)
        if active_session:
            session, _bill = charging_session_service.end_session(active_session.session_id, f"pile fault: {reason}")
            if queue.charging_car:
                remaining = max(0.0, session.target_amount - session.current_amount)
                if remaining > 0:
                    queue.charging_car.requested_amount = remaining
                    queue.charging_car.queue_position = "WAITING_AREA"
                    queue.charging_car.assigned_pile_id = None
                    requeue_cars.append(queue.charging_car)

        if queue.waiting_car:
            queue.waiting_car.queue_position = "WAITING_AREA"
            queue.waiting_car.assigned_pile_id = None
            requeue_cars.append(queue.waiting_car)

        queue.charging_car = None
        queue.waiting_car = None
        pile_management_service.mark_fault(pile_id)

        candidate_piles = self._same_type_piles_except(pile_id)
        if strategy == "time":
            dispatched = scheduling_service.time_sequence_dispatch(requeue_cars, candidate_piles)
        else:
            dispatched = scheduling_service.priority_dispatch(requeue_cars, candidate_piles)

        self._put_not_dispatched_back(requeue_cars, dispatched)
        return record, dispatched

    def recover_pile(self, pile_id: str):
        """故障恢复后重新启用充电桩，并按时间顺序尝试重新调度同类型车辆。"""
        pile_management_service.power_on(pile_id)
        fault_id = self.latest_fault_by_pile.get(pile_id)
        record = self.records.get(fault_id) if fault_id else self._get_latest_record_from_database(pile_id)
        if record and record.status != "RECOVERED":
            record.recover()
            self.records[record.fault_id] = record
            self.latest_fault_by_pile[pile_id] = record.fault_id
            self._save_record_to_database(record)
        moved_cars = self._collect_waiting_cars_from_same_type_piles(pile_id)
        candidate_piles = self._same_type_piles_including(pile_id)
        dispatched = scheduling_service.time_sequence_dispatch(moved_cars, candidate_piles)
        self._put_not_dispatched_back(moved_cars, dispatched)
        scheduling_service.dispatch_waiting_cars()
        return record, dispatched

    def priority_dispatch(self, pile_id: str):
        """优先级调度：优先安排故障影响范围内被转移出来的车辆。"""
        cars = self._collect_waiting_cars_from_same_type_piles(pile_id)
        dispatched = scheduling_service.priority_dispatch(cars, self._same_type_piles_including(pile_id))
        self._put_not_dispatched_back(cars, dispatched)
        return dispatched

    def time_sequence_dispatch(self, pile_id: str):
        """时间顺序调度：按排队号先后顺序重新安排同类型车辆。"""
        cars = self._collect_waiting_cars_from_same_type_piles(pile_id)
        dispatched = scheduling_service.time_sequence_dispatch(cars, self._same_type_piles_including(pile_id))
        self._put_not_dispatched_back(cars, dispatched)
        return dispatched

    def list_records(self):
        records = self._list_records_from_database()
        if records is not None:
            for record in records:
                self.records[record.fault_id] = record
                self.latest_fault_by_pile.setdefault(record.pile_id, record.fault_id)
            return records
        return sorted(self.records.values(), key=lambda item: item.fault_time, reverse=True)

    def _same_type_piles_except(self, pile_id: str):
        group = FAST_PILES if pile_id in FAST_PILES else SLOW_PILES
        return [item for item in group if item != pile_id]

    def _same_type_piles_including(self, pile_id: str):
        return list(FAST_PILES if pile_id in FAST_PILES else SLOW_PILES)

    def _collect_waiting_cars_from_same_type_piles(self, pile_id: str):
        cars = []
        for candidate in self._same_type_piles_including(pile_id):
            queue = scheduling_service.pile_queues[candidate]
            if queue.waiting_car:
                car = queue.waiting_car
                queue.waiting_car = None
                car.queue_position = "WAITING_AREA"
                car.assigned_pile_id = None
                cars.append(car)
        return cars

    @staticmethod
    def _put_not_dispatched_back(cars: list[WaitingCar], dispatched: list[WaitingCar]):
        """未能进入候选充电桩队列的车辆回到等候区，避免车辆状态丢失。"""
        from services.queue_service import queue_service
        dispatched_set = set(id(car) for car in dispatched)
        for car in cars:
            if id(car) not in dispatched_set and not queue_service.waiting_queue.get_by_user(car.user_id):
                queue_service.waiting_queue.add_car(car)

    def _load_records_from_database(self):
        records = self._list_records_from_database()
        if records is None:
            return
        for record in records:
            self.records[record.fault_id] = record
            self.latest_fault_by_pile.setdefault(record.pile_id, record.fault_id)

    def _save_record_to_database(self, record: FaultRecord):
        try:
            self.repository.save_record(record)
        except Exception:
            pass

    def _get_latest_record_from_database(self, pile_id: str):
        try:
            return self.repository.get_latest_by_pile(pile_id)
        except Exception:
            return None

    def _list_records_from_database(self):
        try:
            return self.repository.list_records()
        except Exception:
            return None


fault_recovery_service = FaultRecoveryService()

