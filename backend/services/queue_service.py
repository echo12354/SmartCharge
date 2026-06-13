"""排队与充电请求服务。

本服务同时维护充电请求和等候区队列：提交请求后生成 F/T 排队号，
等待调度服务把车辆移动到对应类型的充电桩队列。同一用户可持有多个未完成请求（多辆车）。
"""

from config.settings import MAX_ACTIVE_REQUESTS_PER_USER
from models.charging_request import ChargingRequest
from models.waiting_car import WaitingCar
from models.waiting_queue import WaitingQueue
from repositories.request_repository import RequestRepository
from utils.validators import normalize_charge_mode


class WaitingAreaFullError(ValueError):
    """Raised when a new request cannot enter the waiting area."""


class QueueService:
    def __init__(self):
        self.waiting_queue = WaitingQueue()
        self.requests_by_id: dict[str, ChargingRequest] = {}
        self.active_requests_by_user: dict[str, set[str]] = {}
        self.repository = RequestRepository()
        self._load_active_requests_from_database()

    def submit_request(
        self,
        user_id: str,
        charge_mode: str,
        amount: float,
        vehicle_label: str = "",
        battery_capacity: float | None = None,
    ):
        """提交充电请求。

        同一用户可同时提交多个请求，每个请求对应一辆车；受 `MAX_ACTIVE_REQUESTS_PER_USER` 限制。
        """
        mode = normalize_charge_mode(charge_mode)
        amount = float(amount)
        if amount <= 0:
            raise ValueError("requested amount must be positive")
        capacity = float(battery_capacity or 0)
        if capacity < 0:
            raise ValueError("battery capacity cannot be negative")

        active_count = len(self._list_active_request_ids(user_id))
        if active_count >= MAX_ACTIVE_REQUESTS_PER_USER:
            raise ValueError(f"user can have at most {MAX_ACTIVE_REQUESTS_PER_USER} active charging requests")
        if not self.waiting_queue.has_space():
            raise WaitingAreaFullError("等候区已满，请稍后再试")

        label = (vehicle_label or "").strip()
        request = ChargingRequest(
            user_id=user_id,
            charge_mode=mode,
            requested_amount=amount,
            vehicle_label=label,
            battery_capacity=capacity,
        )
        car = WaitingCar(
            user_id=user_id,
            request_id=request.request_id,
            charge_mode=mode,
            requested_amount=amount,
            vehicle_label=label,
            battery_capacity=capacity,
        )
        queue_number = self.waiting_queue.add_car(car)
        request.assign_queue_number(queue_number)
        request.status = "WAITING"
        self.requests_by_id[request.request_id] = request
        self._track_active_request(request)
        self._save_request_to_database(request)

        from services.scheduling_service import scheduling_service
        scheduling_service.dispatch_waiting_cars()
        return request

    def modify_amount(self, user_id: str, amount: float, request_id: str | None = None):
        """修改请求电量。电量变化不会改变车辆在同一队列中的先后顺序，因此排队号保持不变。"""
        request = self._get_active_request_for_user(user_id, request_id)
        self._ensure_modifiable(request)
        amount = float(amount)
        if amount <= 0:
            raise ValueError("requested amount must be positive")
        request.change_amount(amount)
        car = self.waiting_queue.get_by_request_id(request.request_id)
        if car:
            car.requested_amount = amount
        self._save_request_to_database(request)
        return request

    def modify_mode(self, user_id: str, charge_mode: str, request_id: str | None = None):
        """修改充电模式。模式变化后需要移出原队列并按新模式重新排队。"""
        request = self._get_active_request_for_user(user_id, request_id)
        self._ensure_modifiable(request)
        mode = normalize_charge_mode(charge_mode)
        old_car = self.waiting_queue.remove_by_request_id(request.request_id)
        if not old_car:
            raise ValueError("request can only be modified in waiting area")
        request.change_mode(mode)
        new_car = WaitingCar(
            user_id=user_id,
            request_id=request.request_id,
            charge_mode=mode,
            requested_amount=request.requested_amount,
            vehicle_label=request.vehicle_label,
            battery_capacity=request.battery_capacity,
        )
        queue_number = self.waiting_queue.add_car(new_car)
        request.assign_queue_number(queue_number)
        request.status = "WAITING"
        self._save_request_to_database(request)
        return request

    def cancel_request(self, user_id: str, request_id: str | None = None):
        """取消指定请求，并从等候区或充电桩队列中移除对应车辆。"""
        request = self._get_active_request_for_user(user_id, request_id)
        from services.scheduling_service import scheduling_service
        if self.waiting_queue.remove_by_request_id(request.request_id):
            request.cancel()
            self._untrack_active_request(request)
            self._save_request_to_database(request)
            scheduling_service.dispatch_waiting_cars()
            return request
        session, _bill = scheduling_service.cancel_request(request.request_id, "request cancelled")
        if session:
            request = self.get_request(request.request_id) or request
            return request
        if scheduling_service.remove_request_from_pile_queues(request.request_id):
            scheduling_service.dispatch_waiting_cars()
        request.cancel()
        self._untrack_active_request(request)
        self._save_request_to_database(request)
        return request

    def list_active_requests(self, user_id: str):
        return [
            request for request in (
                self.get_request(request_id) for request_id in self._list_active_request_ids(user_id)
            ) if request
        ]

    def query_request_state(self, user_id: str, request_id: str):
        request = self._get_active_request_for_user(user_id, request_id)
        return self._build_request_state(request)

    def query_car_state(self, user_id: str):
        """兼容旧接口：返回该用户全部车辆的汇总状态。"""
        vehicles = [self._build_request_state(request) for request in self.list_active_requests(user_id)]
        primary = vehicles[0] if len(vehicles) == 1 else None
        return {
            "vehicles": vehicles,
            "totalActive": len(vehicles),
            "maxAllowed": MAX_ACTIVE_REQUESTS_PER_USER,
            "request": primary["request"] if primary else None,
            "waitingCar": primary["waitingCar"] if primary else None,
            "pileQueue": primary["pileQueue"] if primary else None,
            "chargingSession": primary["chargingSession"] if primary else None,
            "state": primary["state"] if primary else "IDLE",
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

    def get_queue_ahead_count(self, user_id: str, request_id: str | None = None):
        """计算指定请求前方等待车辆数；未传 request_id 时兼容旧行为。"""
        if request_id:
            return self.get_queue_ahead_count_for_request(request_id)
        requests = self.list_active_requests(user_id)
        if not requests:
            return 0
        if len(requests) == 1:
            return self.get_queue_ahead_count_for_request(requests[0].request_id)
        raise ValueError("requestId is required when user has multiple active requests")

    def get_queue_ahead_count_for_request(self, request_id: str):
        waiting = self.waiting_queue.get_by_request_id(request_id)
        if waiting:
            position = self.waiting_queue.position_of_request(request_id)
            return max(0, (position or 1) - 1)
        from services.scheduling_service import scheduling_service
        pile_state = scheduling_service.find_request_in_pile_queues(request_id)
        if not pile_state:
            return 0
        return max(0, int(pile_state.get("queueIndex", 0)))

    def get_admin_queue_info(self):
        from services.scheduling_service import scheduling_service
        rows = []
        for pile_id, queue in scheduling_service.pile_queues.items():
            if queue.charging_car:
                rows.append({
                    "id": len(rows) + 1,
                    "pileName": pile_id,
                    "userId": queue.charging_car.user_id,
                    "requestId": queue.charging_car.request_id,
                    "vehicleLabel": queue.charging_car.vehicle_label,
                    "queueNumber": queue.charging_car.queue_number,
                    "chargeMode": queue.charging_car.charge_mode,
                    "batteryCapacity": queue.charging_car.battery_capacity,
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
                    "requestId": queue.waiting_car.request_id,
                    "vehicleLabel": queue.waiting_car.vehicle_label,
                    "queueNumber": queue.waiting_car.queue_number,
                    "chargeMode": queue.waiting_car.charge_mode,
                    "batteryCapacity": queue.waiting_car.battery_capacity,
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
                "requestId": car.request_id,
                "vehicleLabel": car.vehicle_label,
                "queueNumber": car.queue_number,
                "chargeMode": car.charge_mode,
                "batteryCapacity": car.battery_capacity,
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
                "requestId": queue.waiting_car.request_id,
                "vehicleLabel": queue.waiting_car.vehicle_label,
                "batteryCapacity": queue.waiting_car.battery_capacity,
                "requestedCharge": queue.waiting_car.requested_amount,
                "queueTime": queue.waiting_car.to_dict()["queueTime"],
            })
        return {
            "pileId": pile_id,
            "waitingCars": waiting,
            "currentCharging": queue.charging_car.user_id if queue.charging_car else None,
        }

    def get_admin_queue_info(self):
        from services.scheduling_service import scheduling_service
        rows = []
        for pile_id, queue in scheduling_service.pile_queues.items():
            if queue.charging_car:
                rows.append(self._build_admin_queue_row(pile_id, queue.charging_car, "charging", "充电中"))
            for index, waiting_car in enumerate(queue.waiting_cars, start=2):
                rows.append(self._build_admin_queue_row(pile_id, waiting_car, "waiting", f"桩队列第 {index} 位"))
        for car in self.waiting_queue.cars:
            rows.append(self._build_admin_queue_row("等候区", car, "waiting", "等待中"))
        for index, row in enumerate(rows, start=1):
            row["id"] = index
        return rows

    @staticmethod
    def _build_admin_queue_row(pile_name: str, car: WaitingCar, status_class: str, status: str):
        return {
            "id": 0,
            "pileName": pile_name,
            "userId": car.user_id,
            "requestId": car.request_id,
            "vehicleLabel": car.vehicle_label,
            "queueNumber": car.queue_number,
            "chargeMode": car.charge_mode,
            "batteryCapacity": car.battery_capacity,
            "requestedCharge": car.requested_amount,
            "queueTime": car.to_dict()["queueTime"],
            "status": status,
            "statusClass": status_class,
        }

    def get_queue_for_pile(self, pile_id: str):
        from services.scheduling_service import scheduling_service
        queue = scheduling_service.pile_queues.get(pile_id)
        if not queue:
            return None
        waiting = [
            {
                "username": car.user_id,
                "requestId": car.request_id,
                "vehicleLabel": car.vehicle_label,
                "batteryCapacity": car.battery_capacity,
                "requestedCharge": car.requested_amount,
                "queueTime": car.to_dict()["queueTime"],
            }
            for car in queue.waiting_cars
        ]
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

    def mark_completed_by_request(self, request_id: str):
        request = self.get_request(request_id)
        if request:
            request.mark_completed()
            self._untrack_active_request(request)
            self._save_request_to_database(request)

    def mark_completed_by_user(self, user_id: str):
        """兼容旧接口：仅当用户只剩一个活跃请求时可用。"""
        request_ids = self._list_active_request_ids(user_id)
        if len(request_ids) != 1:
            raise ValueError("requestId is required when user has multiple active requests")
        self.mark_completed_by_request(request_ids[0])

    def _build_request_state(self, request: ChargingRequest):
        waiting_car = self.waiting_queue.get_by_request_id(request.request_id)
        from services.scheduling_service import scheduling_service
        from services.charging_session_service import charging_session_service
        pile_state = scheduling_service.find_request_in_pile_queues(request.request_id)
        session = charging_session_service.get_request_active_session(request.request_id)
        return {
            "request": request.to_dict(),
            "waitingCar": waiting_car.to_dict() if waiting_car else None,
            "pileQueue": pile_state,
            "chargingSession": session.to_dict() if session else None,
            "aheadCount": self.get_queue_ahead_count_for_request(request.request_id),
            "state": self._derive_state(request, waiting_car, pile_state, session),
        }

    def _list_active_request_ids(self, user_id: str) -> list[str]:
        cached = sorted(self.active_requests_by_user.get(user_id, set()))
        if cached:
            return cached
        try:
            requests = self.repository.list_active_requests_by_user(user_id)
        except Exception:
            requests = []
        for request in requests:
            self._cache_request(request)
        return sorted(self.active_requests_by_user.get(user_id, set()))

    def _get_active_request_for_user(self, user_id: str, request_id: str | None = None):
        if request_id:
            request = self.get_request(request_id)
            if not request or request.user_id != user_id:
                raise ValueError("request not found")
            if request.status in ("COMPLETED", "CANCELLED"):
                raise ValueError("active request not found")
            return request

        request_ids = self._list_active_request_ids(user_id)
        if not request_ids:
            raise ValueError("active request not found")
        if len(request_ids) > 1:
            raise ValueError("requestId is required when user has multiple active requests")
        return self.get_request(request_ids[0])

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

    def _get_request_from_database(self, request_id: str):
        if not request_id:
            return None
        try:
            return self.repository.get_request(request_id)
        except Exception:
            return None

    def _save_request_to_database(self, request: ChargingRequest):
        try:
            self.repository.save_request(request)
        except Exception:
            pass

    def _track_active_request(self, request: ChargingRequest):
        self.active_requests_by_user.setdefault(request.user_id, set()).add(request.request_id)

    def _untrack_active_request(self, request: ChargingRequest):
        active = self.active_requests_by_user.get(request.user_id)
        if not active:
            return
        active.discard(request.request_id)
        if not active:
            self.active_requests_by_user.pop(request.user_id, None)

    def _cache_request(self, request: ChargingRequest):
        self.requests_by_id[request.request_id] = request
        if request.status not in ("COMPLETED", "CANCELLED"):
            self._track_active_request(request)


queue_service = QueueService()
