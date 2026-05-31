"""Queue service.

This service intentionally combines charging request and waiting queue behavior.
Do not split it into ChargingRequestService or WaitingQueueService.
"""

from models.charging_request import ChargingRequest
from models.waiting_car import WaitingCar
from models.waiting_queue import WaitingQueue
from utils.validators import normalize_charge_mode


class QueueService:
    def __init__(self):
        self.waiting_queue = WaitingQueue()
        self.requests_by_id: dict[str, ChargingRequest] = {}
        self.active_request_by_user: dict[str, str] = {}

    def submit_request(self, user_id: str, charge_mode: str, amount: float):
        mode = normalize_charge_mode(charge_mode)
        amount = float(amount)
        if amount <= 0:
            raise ValueError("requested amount must be positive")
        if user_id in self.active_request_by_user:
            existing = self.requests_by_id[self.active_request_by_user[user_id]]
            if existing.status not in ("COMPLETED", "CANCELLED"):
                raise ValueError("user already has active charging request")

        request = ChargingRequest(user_id=user_id, charge_mode=mode, requested_amount=amount)
        car = WaitingCar(
            user_id=user_id,
            request_id=request.request_id,
            charge_mode=mode,
            requested_amount=amount,
        )
        queue_number = self.waiting_queue.add_car(car)
        request.assign_queue_number(queue_number)
        request.status = "WAITING"
        self.requests_by_id[request.request_id] = request
        self.active_request_by_user[user_id] = request.request_id

        from services.scheduling_service import scheduling_service
        scheduling_service.dispatch_waiting_cars()
        return request

    def modify_amount(self, user_id: str, amount: float):
        request = self._get_active_request_for_user(user_id)
        self._ensure_modifiable(request)
        amount = float(amount)
        if amount <= 0:
            raise ValueError("requested amount must be positive")
        request.change_amount(amount)
        car = self.waiting_queue.get_by_user(user_id)
        if car:
            car.requested_amount = amount
        return request

    def modify_mode(self, user_id: str, charge_mode: str):
        request = self._get_active_request_for_user(user_id)
        self._ensure_modifiable(request)
        mode = normalize_charge_mode(charge_mode)
        old_car = self.waiting_queue.remove_by_user(user_id)
        if not old_car:
            raise ValueError("request can only be modified in waiting area")
        request.change_mode(mode)
        new_car = WaitingCar(
            user_id=user_id,
            request_id=request.request_id,
            charge_mode=mode,
            requested_amount=request.requested_amount,
        )
        queue_number = self.waiting_queue.add_car(new_car)
        request.assign_queue_number(queue_number)
        request.status = "WAITING"
        return request

    def cancel_request(self, user_id: str):
        request = self._get_active_request_for_user(user_id)
        self.waiting_queue.remove_by_user(user_id)
        from services.scheduling_service import scheduling_service
        scheduling_service.remove_user_from_pile_queues(user_id)
        request.cancel()
        self.active_request_by_user.pop(user_id, None)
        return request

    def query_car_state(self, user_id: str):
        request = self.requests_by_id.get(self.active_request_by_user.get(user_id, ""))
        waiting_car = self.waiting_queue.get_by_user(user_id)
        from services.scheduling_service import scheduling_service
        from services.charging_session_service import charging_session_service
        pile_state = scheduling_service.find_user_in_pile_queues(user_id)
        session = charging_session_service.get_user_active_session(user_id)
        return {
            "request": request.to_dict() if request else None,
            "waitingCar": waiting_car.to_dict() if waiting_car else None,
            "pileQueue": pile_state,
            "chargingSession": session.to_dict() if session else None,
            "state": self._derive_state(request, waiting_car, pile_state, session),
        }

    def query_queue_state(self):
        from services.scheduling_service import scheduling_service
        return {
            "waitingArea": self.waiting_queue.to_dict(),
            "pileQueues": scheduling_service.get_all_pile_queues(),
        }

    def query_charge_area_state(self):
        from services.pile_management_service import pile_management_service
        from services.scheduling_service import scheduling_service
        return {
            "queueCarCount": len(self.waiting_queue.cars),
            "chargingCarCount": sum(
                1 for queue in scheduling_service.pile_queues.values() if queue.charging_car
            ),
            "piles": [pile.to_dict() for pile in pile_management_service.list_piles()],
        }

    def get_queue_ahead_count(self, user_id: str):
        waiting = self.waiting_queue.get_by_user(user_id)
        if waiting:
            position = self.waiting_queue.position_of(user_id)
            return max(0, (position or 1) - 1)
        from services.scheduling_service import scheduling_service
        pile_state = scheduling_service.find_user_in_pile_queues(user_id)
        if not pile_state:
            return 0
        return 0 if pile_state["queuePosition"] == "CHARGING" else 1

    def get_admin_queue_info(self):
        from services.scheduling_service import scheduling_service
        rows = []
        for pile_id, queue in scheduling_service.pile_queues.items():
            if queue.charging_car:
                rows.append({
                    "id": len(rows) + 1,
                    "pileName": pile_id,
                    "userId": queue.charging_car.user_id,
                    "requestedCharge": queue.charging_car.requested_amount,
                    "queueTime": queue.charging_car.to_dict()["queueTime"],
                    "status": "充电中",
                    "statusClass": "charging",
                })
            if queue.waiting_car:
                rows.append({
                    "id": len(rows) + 1,
                    "pileName": pile_id,
                    "userId": queue.waiting_car.user_id,
                    "requestedCharge": queue.waiting_car.requested_amount,
                    "queueTime": queue.waiting_car.to_dict()["queueTime"],
                    "status": "排队中 第1位",
                    "statusClass": "waiting",
                })
        for car in self.waiting_queue.cars:
            rows.append({
                "id": len(rows) + 1,
                "pileName": "等待区",
                "userId": car.user_id,
                "requestedCharge": car.requested_amount,
                "queueTime": car.to_dict()["queueTime"],
                "status": "等待中",
                "statusClass": "waiting",
            })
        return rows

    def get_queue_for_pile(self, pile_id: str):
        from services.scheduling_service import scheduling_service
        queue = scheduling_service.pile_queues.get(pile_id)
        if not queue:
            return None
        waiting = []
        if queue.waiting_car:
            waiting.append({
                "username": queue.waiting_car.user_id,
                "requestedCharge": queue.waiting_car.requested_amount,
                "queueTime": queue.waiting_car.to_dict()["queueTime"],
            })
        return {
            "pileId": pile_id,
            "waitingCars": waiting,
            "currentCharging": queue.charging_car.user_id if queue.charging_car else None,
        }

    def get_request(self, request_id: str):
        return self.requests_by_id.get(request_id)

    def mark_dispatched(self, car: WaitingCar, pile_id: str):
        request = self.requests_by_id.get(car.request_id)
        if request:
            request.assign_pile(pile_id)

    def mark_charging(self, car: WaitingCar):
        request = self.requests_by_id.get(car.request_id)
        if request:
            request.mark_charging()

    def mark_completed_by_user(self, user_id: str):
        request_id = self.active_request_by_user.pop(user_id, None)
        if request_id and request_id in self.requests_by_id:
            self.requests_by_id[request_id].mark_completed()

    def _get_active_request_for_user(self, user_id: str):
        request_id = self.active_request_by_user.get(user_id)
        if not request_id:
            raise ValueError("active request not found")
        return self.requests_by_id[request_id]

    def _ensure_modifiable(self, request: ChargingRequest):
        if request.status != "WAITING":
            raise ValueError("request can only be modified while waiting")

    @staticmethod
    def _derive_state(request, waiting_car, pile_state, session):
        if session:
            return "CHARGING"
        if pile_state:
            return pile_state.get("queuePosition", "PILE_QUEUE")
        if waiting_car:
            return "WAITING_AREA"
        if request:
            return request.status
        return "IDLE"


queue_service = QueueService()
