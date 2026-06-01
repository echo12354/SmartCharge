"""Charging scheduling service."""

from config.settings import FAST_PILES, PILE_POWER, SLOW_PILES
from models.dispatch_decision import DispatchDecision
from models.pile_queue import PileQueue
from models.waiting_car import WaitingCar
from repositories.dispatch_repository import DispatchRepository
from services.charging_session_service import charging_session_service
from services.pile_management_service import pile_management_service


class SchedulingService:
    def __init__(self):
        self.pile_queues: dict[str, PileQueue] = {
            pile_id: PileQueue(pile_id) for pile_id in (*FAST_PILES, *SLOW_PILES)
        }
        self.decisions: list[DispatchDecision] = []
        self.repository = DispatchRepository()
        self.engine_running = True
        self._load_recent_decisions_from_database()

    def dispatch_waiting_cars(self):
        if not self.engine_running:
            return self.get_statistics()
        self.refresh_finished_sessions()
        from services.queue_service import queue_service
        for mode in ("fast", "slow"):
            while True:
                cars = queue_service.waiting_queue.cars_by_mode(mode)
                if not cars:
                    break
                car = cars[0]
                pile_id, expected = self._select_optimal_pile(car)
                if not pile_id:
                    break
                queue_service.waiting_queue.remove_car(car)
                self.pile_queues[pile_id].add_car(car)
                queue_service.mark_dispatched(car, pile_id)
                decision = DispatchDecision(
                    request_id=car.request_id,
                    user_id=car.user_id,
                    selected_pile_id=pile_id,
                    strategy="SHORTEST_COMPLETION_TIME",
                    reason="selected available pile with shortest estimated completion time",
                    expected_completion_hours=expected,
                )
                self._record_decision(decision)
                if car.queue_position == "CHARGING":
                    self._start_car_session(car, pile_id)
        return self.get_statistics()

    def start_charging(self, pile_id: str, user_id: str | None = None):
        queue = self._require_pile_queue(pile_id)
        car = queue.charging_car
        if not car:
            raise ValueError("no car in charging slot")
        if user_id and car.user_id != user_id:
            raise ValueError("charging slot is occupied by another user")
        return self._start_car_session(car, pile_id)

    def end_charging(self, session_id: str, reason: str = "manual stop"):
        session = charging_session_service.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        pile_queue = self._require_pile_queue(session.pile_id)
        self._remove_charging_car_without_promotion(pile_queue, session.user_id)
        session, bill = charging_session_service.end_session(session_id, reason)
        from services.queue_service import queue_service
        queue_service.mark_completed_by_user(session.user_id)
        promoted = pile_queue.promote_waiting_car()
        if promoted:
            self._start_car_session(promoted, session.pile_id)
        self.dispatch_waiting_cars()
        return session, bill

    def refresh_finished_sessions(self):
        closed = charging_session_service.close_completed_sessions()
        if not closed:
            return []
        from services.queue_service import queue_service
        for session, _bill in closed:
            pile_queue = self.pile_queues.get(session.pile_id)
            if pile_queue:
                self._remove_charging_car_without_promotion(pile_queue, session.user_id)
                promoted = pile_queue.promote_waiting_car()
                if promoted:
                    self._start_car_session(promoted, session.pile_id)
            queue_service.mark_completed_by_user(session.user_id)
        return closed

    def priority_dispatch(self, cars: list[WaitingCar], candidate_piles: list[str]):
        return self._dispatch_specific_cars(cars, candidate_piles, "PRIORITY")

    def time_sequence_dispatch(self, cars: list[WaitingCar], candidate_piles: list[str]):
        ordered = sorted(cars, key=lambda car: self._queue_number_sort_key(car.queue_number))
        return self._dispatch_specific_cars(ordered, candidate_piles, "TIME_SEQUENCE")

    def remove_user_from_pile_queues(self, user_id: str):
        removed = None
        for queue in self.pile_queues.values():
            car = queue.remove_user(user_id)
            if car:
                removed = car
        return removed

    def find_user_in_pile_queues(self, user_id: str):
        for pile_id, queue in self.pile_queues.items():
            for car in queue.cars():
                if car.user_id == user_id:
                    return {
                        "pileId": pile_id,
                        "queuePosition": car.queue_position,
                        "car": car.to_dict(),
                    }
        return None

    def get_all_pile_queues(self):
        return {pile_id: queue.to_dict() for pile_id, queue in self.pile_queues.items()}

    def get_pile_queue(self, pile_id: str):
        queue = self.pile_queues.get(pile_id)
        return queue.to_dict() if queue else None

    def start_engine(self):
        self.engine_running = True
        return self.get_statistics()

    def stop_engine(self):
        self.engine_running = False
        return self.get_statistics()

    def get_statistics(self):
        occupied = {}
        for pile_id, queue in self.pile_queues.items():
            count = len(queue.cars())
            occupied[pile_id] = round(count / queue.capacity * 100, 1)
        return {
            "engineRunning": self.engine_running,
            "pileQueues": self.get_all_pile_queues(),
            "pileUtilization": occupied,
            "queueCapacity": {
                pile_id: {
                    "total": queue.capacity,
                    "occupied": len(queue.cars()),
                    "available": queue.capacity - len(queue.cars()),
                }
                for pile_id, queue in self.pile_queues.items()
            },
            "totalDispatched": self._decision_count(),
            "decisionCount": self._decision_count(),
            "recentDecisions": [item.to_dict() for item in self.decisions[-10:]],
        }

    def _select_optimal_pile(self, car: WaitingCar):
        candidate_ids = FAST_PILES if car.charge_mode == "fast" else SLOW_PILES
        best_pile_id = None
        best_time = None
        for pile_id in candidate_ids:
            pile = pile_management_service.get_pile(pile_id)
            queue = self.pile_queues[pile_id]
            if not pile or not pile.is_enabled or not queue.has_space():
                continue
            completion_time = self._estimate_completion_time(queue, car.requested_amount, pile.power)
            if best_time is None or completion_time < best_time:
                best_time = completion_time
                best_pile_id = pile_id
        return best_pile_id, best_time

    @staticmethod
    def _estimate_completion_time(queue: PileQueue, amount: float, power: float):
        wait_time = 0.0
        active = charging_session_service.get_pile_active_session(queue.pile_id)
        if active:
            wait_time += active.remaining_hours()
        elif queue.charging_car:
            wait_time += queue.charging_car.requested_amount / power
        if queue.waiting_car:
            wait_time += queue.waiting_car.requested_amount / power
        return wait_time + amount / power

    def _start_car_session(self, car: WaitingCar, pile_id: str):
        from services.queue_service import queue_service
        session = charging_session_service.create_and_start(
            user_id=car.user_id,
            pile_id=pile_id,
            amount=car.requested_amount,
            request_id=car.request_id,
        )
        queue_service.mark_charging(car)
        return session

    def _dispatch_specific_cars(self, cars: list[WaitingCar], candidate_piles: list[str], strategy: str):
        dispatched = []
        for car in cars:
            for pile_id in candidate_piles:
                pile = pile_management_service.get_pile(pile_id)
                queue = self.pile_queues.get(pile_id)
                if not pile or not pile.is_enabled or not queue or not queue.has_space():
                    continue
                queue.add_car(car)
                if car.queue_position == "CHARGING":
                    self._start_car_session(car, pile_id)
                decision = DispatchDecision(
                    request_id=car.request_id,
                    user_id=car.user_id,
                    selected_pile_id=pile_id,
                    strategy=strategy,
                    reason=f"{strategy.lower()} dispatch",
                    expected_completion_hours=car.requested_amount / PILE_POWER[pile_id],
                )
                self._record_decision(decision)
                dispatched.append(car)
                break
        return dispatched

    def _require_pile_queue(self, pile_id: str):
        queue = self.pile_queues.get(pile_id)
        if not queue:
            raise ValueError("pile queue not found")
        return queue

    @staticmethod
    def _remove_charging_car_without_promotion(queue: PileQueue, user_id: str):
        if queue.charging_car and queue.charging_car.user_id == user_id:
            queue.charging_car = None
            return
        if queue.waiting_car and queue.waiting_car.user_id == user_id:
            queue.waiting_car = None

    @staticmethod
    def _queue_number_sort_key(queue_number: str):
        try:
            return int(queue_number[1:])
        except Exception:
            return 0

    def _record_decision(self, decision: DispatchDecision):
        self.decisions.append(decision)
        try:
            self.repository.save_decision(decision)
        except Exception:
            pass

    def _load_recent_decisions_from_database(self):
        try:
            self.decisions = self.repository.list_recent_decisions(10)
        except Exception:
            pass

    def _decision_count(self):
        try:
            return self.repository.count_decisions()
        except Exception:
            return len(self.decisions)


scheduling_service = SchedulingService()
