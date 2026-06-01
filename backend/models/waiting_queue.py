"""等候区队列模型。

车辆提交请求后先进入等候区，再由调度服务移动到匹配的充电桩队列。
"""

from dataclasses import dataclass, field

from config.settings import WAITING_QUEUE_CAPACITY
from models.waiting_car import WaitingCar


@dataclass
class WaitingQueue:
    """充电站等候区。

    快充和慢充分别维护 F/T 计数器，队列总容量受 `capacity` 限制。
    """

    capacity: int = WAITING_QUEUE_CAPACITY
    cars: list[WaitingCar] = field(default_factory=list)
    fast_counter: int = 0
    slow_counter: int = 0

    def has_space(self) -> bool:
        return len(self.cars) < self.capacity

    def add_car(self, car: WaitingCar) -> str:
        """加入等候区并生成排队号：快充 F 开头，慢充 T 开头。"""
        if not self.has_space():
            raise ValueError("waiting queue is full")
        if car.charge_mode == "fast":
            self.fast_counter += 1
            car.queue_number = f"F{self.fast_counter}"
        else:
            self.slow_counter += 1
            car.queue_number = f"T{self.slow_counter}"
        car.queue_position = "WAITING_AREA"
        car.assigned_pile_id = None
        self.cars.append(car)
        return car.queue_number

    def remove_by_user(self, user_id: str) -> WaitingCar | None:
        for car in list(self.cars):
            if car.user_id == user_id:
                self.cars.remove(car)
                return car
        return None

    def remove_car(self, car: WaitingCar) -> bool:
        if car in self.cars:
            self.cars.remove(car)
            return True
        return False

    def get_by_user(self, user_id: str) -> WaitingCar | None:
        return next((car for car in self.cars if car.user_id == user_id), None)

    def cars_by_mode(self, mode: str) -> list[WaitingCar]:
        """按充电模式取车，并保持先到先服务顺序。"""
        return sorted(
            [car for car in self.cars if car.charge_mode == mode],
            key=lambda car: car.join_time,
        )

    def position_of(self, user_id: str) -> int | None:
        car = self.get_by_user(user_id)
        if not car:
            return None
        same_mode = self.cars_by_mode(car.charge_mode)
        return same_mode.index(car) + 1

    def to_dict(self):
        return {
            "capacity": self.capacity,
            "count": len(self.cars),
            "cars": [car.to_dict() for car in self.cars],
        }

