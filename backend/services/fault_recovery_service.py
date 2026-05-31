"""Fault handling and recovery service."""

from config.settings import FAST_PILES, SLOW_PILES
from models.fault_record import FaultRecord
from models.waiting_car import WaitingCar
from services.charging_session_service import charging_session_service
from services.pile_management_service import pile_management_service
from services.scheduling_service import scheduling_service


class FaultRecoveryService:
    def __init__(self):
        self.records: dict[str, FaultRecord] = {}
        self.latest_fault_by_pile: dict[str, str] = {}

    def power_off_with_fault(self, pile_id: str, reason: str = "manual power off", strategy: str = "priority"):
        pile = pile_management_service.get_pile(pile_id)
        if not pile:
            raise ValueError("pile not found")
        queue = scheduling_service.pile_queues[pile_id]
        affected = queue.cars()
        affected_ids = [car.user_id for car in affected]
        record = FaultRecord(pile_id=pile_id, reason=reason, affected_car_ids=affected_ids)
        self.records[record.fault_id] = record
        self.latest_fault_by_pile[pile_id] = record.fault_id

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
        pile_management_service.power_on(pile_id)
        fault_id = self.latest_fault_by_pile.get(pile_id)
        record = self.records.get(fault_id) if fault_id else None
        if record and record.status != "RECOVERED":
            record.recover()
        moved_cars = self._collect_waiting_cars_from_same_type_piles(pile_id)
        candidate_piles = self._same_type_piles_including(pile_id)
        dispatched = scheduling_service.time_sequence_dispatch(moved_cars, candidate_piles)
        self._put_not_dispatched_back(moved_cars, dispatched)
        scheduling_service.dispatch_waiting_cars()
        return record, dispatched

    def priority_dispatch(self, pile_id: str):
        cars = self._collect_waiting_cars_from_same_type_piles(pile_id)
        dispatched = scheduling_service.priority_dispatch(cars, self._same_type_piles_including(pile_id))
        self._put_not_dispatched_back(cars, dispatched)
        return dispatched

    def time_sequence_dispatch(self, pile_id: str):
        cars = self._collect_waiting_cars_from_same_type_piles(pile_id)
        dispatched = scheduling_service.time_sequence_dispatch(cars, self._same_type_piles_including(pile_id))
        self._put_not_dispatched_back(cars, dispatched)
        return dispatched

    def list_records(self):
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
        from services.queue_service import queue_service
        dispatched_set = set(id(car) for car in dispatched)
        for car in cars:
            if id(car) not in dispatched_set and not queue_service.waiting_queue.get_by_user(car.user_id):
                queue_service.waiting_queue.add_car(car)


fault_recovery_service = FaultRecoveryService()

