"""充电桩队列模型。

每个桩维护 1 个充电位和最多 M-1 个等待位，总容量为 M。
"""

from dataclasses import dataclass, field

from config.settings import PILE_QUEUE_CAPACITY
from models.waiting_car import WaitingCar


@dataclass
class PileQueue:
    """某一台充电桩对应的队列状态。"""

    pile_id: str
    capacity: int = PILE_QUEUE_CAPACITY
    charging_car: WaitingCar | None = None
    waiting_cars: list[WaitingCar] = field(default_factory=list)

    @property
    def max_waiting_slots(self) -> int:
        return max(0, self.capacity - 1)

    def has_space(self) -> bool:
        if self.charging_car is None:
            return True
        return len(self.waiting_cars) < self.max_waiting_slots

    def is_empty(self) -> bool:
        return self.charging_car is None and not self.waiting_cars

    def add_car(self, car: WaitingCar) -> str:
        if self.charging_car is None:
            self.charging_car = car
            car.queue_position = "CHARGING"
        elif len(self.waiting_cars) < self.max_waiting_slots:
            self.waiting_cars.append(car)
            car.queue_position = "PILE_QUEUE"
        else:
            raise ValueError("pile queue is full")
        car.assigned_pile_id = self.pile_id
        return car.queue_position

    def remove_user(self, user_id: str) -> WaitingCar | None:
        if self.charging_car and self.charging_car.user_id == user_id:
            car = self.charging_car
            self.charging_car = None
            self.promote_waiting_car()
            return car
        for index, waiting in enumerate(self.waiting_cars):
            if waiting.user_id == user_id:
                return self.waiting_cars.pop(index)
        return None

    def remove_by_request_id(self, request_id: str) -> WaitingCar | None:
        if self.charging_car and self.charging_car.request_id == request_id:
            car = self.charging_car
            self.charging_car = None
            self.promote_waiting_car()
            return car
        for index, waiting in enumerate(self.waiting_cars):
            if waiting.request_id == request_id:
                return self.waiting_cars.pop(index)
        return None

    def promote_waiting_car(self) -> WaitingCar | None:
        if self.charging_car is None and self.waiting_cars:
            self.charging_car = self.waiting_cars.pop(0)
            self.charging_car.queue_position = "CHARGING"
            return self.charging_car
        return None

    def cars(self) -> list[WaitingCar]:
        cars = []
        if self.charging_car:
            cars.append(self.charging_car)
        cars.extend(self.waiting_cars)
        return cars

    def to_dict(self):
        return {
            "pileId": self.pile_id,
            "capacity": self.capacity,
            "availableCapacity": int(self.charging_car is None) + max(0, self.max_waiting_slots - len(self.waiting_cars)),
            "chargingCar": self.charging_car.to_dict() if self.charging_car else None,
            "waitingCar": self.waiting_cars[0].to_dict() if self.waiting_cars else None,
            "waitingCars": [car.to_dict() for car in self.waiting_cars],
        }
