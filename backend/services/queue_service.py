"""排队与充电请求服务。

本服务同时维护充电请求和等候区队列：提交请求后生成 F/T 排队号，
等待调度服务把车辆移动到对应类型的充电桩队列。
"""

from models.charging_request import ChargingRequest
from models.waiting_car import WaitingCar
from models.waiting_queue import WaitingQueue
from repositories.request_repository import RequestRepository
from utils.validators import normalize_charge_mode


class QueueService:
    def __init__(self):
        self.waiting_queue = WaitingQueue()
        self.requests_by_id: dict[str, ChargingRequest] = {}
        self.active_request_by_user: dict[str, str] = {}
        self.repository = RequestRepository()
        self._load_active_requests_from_database()

    def submit_request(self, user_id: str, charge_mode: str, amount: float):
        """提交充电请求。

        等候区容量由 `WaitingQueue` 控制；快充生成 F 序号，慢充生成 T 序号。
        """
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
        self._save_request_to_database(request)

        from services.scheduling_service import scheduling_service
        scheduling_service.dispatch_waiting_cars()
        return request

    def modify_amount(self, user_id: str, amount: float):
        """修改请求电量。

        电量变化不会改变车辆在同一队列中的先后顺序，因此排队号保持不变。
        """
        request = self._get_active_request_for_user(user_id)
        self._ensure_modifiable(request)
        amount = float(amount)
        if amount <= 0:
            raise ValueError("requested amount must be positive")
        request.change_amount(amount)
        car = self.waiting_queue.get_by_user(user_id)
        if car:
            car.requested_amount = amount
        self._save_request_to_database(request)
        return request

    def modify_mode(self, user_id: str, charge_mode: str):
        """修改充电模式。

        快充和慢充使用不同队列，模式变化后需要移出原队列并按新模式重新排队。
        """
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
        self._save_request_to_database(request)
        return request

    def cancel_request(self, user_id: str):
        """取消当前请求，并从等候区或充电桩队列中移除车辆。"""
        request = self._get_active_request_for_user(user_id)
        self.waiting_queue.remove_by_user(user_id)
        from services.scheduling_service import scheduling_service
        scheduling_service.remove_user_from_pile_queues(user_id)
        request.cancel()
        self.active_request_by_user.pop(user_id, None)
        self._save_request_to_database(request)
        return request

    def query_car_state(self, user_id: str):
        request = self._get_cached_or_database_active_request(user_id)
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
        """计算用户前方等待车辆数，用于客户端展示排队进度。"""
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
        request = self.requests_by_id.get(request_id) or self._get_request_from_database(request_id)
        if request:
            self._cache_request(request)
        return request

    def mark_dispatched(self, car: WaitingCar, pile_id: str):
        request = self.get_request(car.request_id)
        if request:
            request.assign_pile(pile_id)
            self._save_request_to_database(request)

    def mark_charging(self, car: WaitingCar):
        request = self.get_request(car.request_id)
        if request:
            request.mark_charging()
            self._save_request_to_database(request)

    def mark_completed_by_user(self, user_id: str):
        request_id = self.active_request_by_user.pop(user_id, None)
        request = self.get_request(request_id) if request_id else self._get_active_request_from_database(user_id)
        if request:
            request.mark_completed()
            self.requests_by_id[request.request_id] = request
            self._save_request_to_database(request)

    def _get_active_request_for_user(self, user_id: str):
        request = self._get_cached_or_database_active_request(user_id)
        if not request:
            raise ValueError("active request not found")
        return request

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

    def _load_active_requests_from_database(self):
        try:
            for request in self.repository.list_active_requests():
                self._cache_request(request)
        except Exception:
            pass

    def _get_cached_or_database_active_request(self, user_id: str):
        request_id = self.active_request_by_user.get(user_id)
        request = self.requests_by_id.get(request_id) if request_id else None
        if request:
            return request
        request = self._get_active_request_from_database(user_id)
        if request:
            self._cache_request(request)
        return request

    def _get_active_request_from_database(self, user_id: str):
        try:
            return self.repository.get_active_request_by_user(user_id)
        except Exception:
            return None

    def _get_request_from_database(self, request_id: str):
        if not request_id:
            return None
        try:
            return self.repository.get_request(request_id)
        except Exception:
            return None

    def _save_request_to_database(self, request: ChargingRequest):
        """MySQL 可用时同步请求状态；失败时继续使用内存数据。"""
        try:
            self.repository.save_request(request)
        except Exception:
            pass

    def _cache_request(self, request: ChargingRequest):
        self.requests_by_id[request.request_id] = request
        if request.status not in ("COMPLETED", "CANCELLED"):
            self.active_request_by_user[request.user_id] = request.request_id


queue_service = QueueService()
