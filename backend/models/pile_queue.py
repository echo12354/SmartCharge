"""Charging pile queue model."""

from dataclasses import dataclass, field

from config.settings import PILE_QUEUE_CAPACITY
from models.waiting_car import WaitingCar


@dataclass
class PileQueue:
    """Runtime queue for one charging pile.

    The first slot is `charging_car`; the remaining `capacity - 1` slots are
    ordered waiting cars. The `waiting_car` property is kept for compatibility
    with existing M=2 code paths.
    """

    pile_id: str
    capacity: int = PILE_QUEUE_CAPACITY
    charging_car: WaitingCar | None = None
    waiting_cars: list[WaitingCar] = field(default_factory=list)

    @property
    def waiting_car(self) -> WaitingCar | None:
        return self.waiting_cars[0] if self.waiting_cars else None

    @waiting_car.setter
    def waiting_car(self, car: WaitingCar | None):
        if car is None:
            if self.waiting_cars:
                self.waiting_cars.pop(0)
            return
        if self.waiting_cars:
            self.waiting_cars[0] = car
        else:
            self.waiting_cars.append(car)

    def has_space(self) -> bool:
        return len(self.cars()) < self.capacity

    def is_empty(self) -> bool:
        return self.charging_car is None and not self.waiting_cars

    def add_car(self, car: WaitingCar) -> str:
        if not self.has_space():
            raise ValueError("pile queue is full")
        if self.charging_car is None:
            self.charging_car = car
            car.queue_position = "CHARGING"
        else:
            self.waiting_cars.append(car)
            car.queue_position = "PILE_QUEUE"
        car.assigned_pile_id = self.pile_id
        return car.queue_position

    def remove_user(self, user_id: str) -> WaitingCar | None:
        if self.charging_car and self.charging_car.user_id == user_id:
            car = self.charging_car
            self.charging_car = None
            self.promote_waiting_car()
            return car
        for car in list(self.waiting_cars):
            if car.user_id == user_id:
                self.waiting_cars.remove(car)
                return car
        return None

    def remove_by_request_id(self, request_id: str) -> WaitingCar | None:
        if self.charging_car and self.charging_car.request_id == request_id:
            car = self.charging_car
            self.charging_car = None
            self.promote_waiting_car()
            return car
        for car in list(self.waiting_cars):
            if car.request_id == request_id:
                self.waiting_cars.remove(car)
                return car
        return None

    def promote_waiting_car(self) -> WaitingCar | None:
        if self.charging_car is None and self.waiting_cars:
            self.charging_car = self.waiting_cars.pop(0)
            self.charging_car.queue_position = "CHARGING"
            return self.charging_car
        return None

    def cars(self) -> list[WaitingCar]:
        return ([self.charging_car] if self.charging_car else []) + list(self.waiting_cars)

    def position_of_request(self, request_id: str) -> int | None:
        for index, car in enumerate(self.cars()):
            if car.request_id == request_id:
                return index
        return None

    def to_dict(self):
        return {
            "pileId": self.pile_id,
            "capacity": self.capacity,
            "availableCapacity": max(0, self.capacity - len(self.cars())),
            "chargingCar": self.charging_car.to_dict() if self.charging_car else None,
            "waitingCar": self.waiting_car.to_dict() if self.waiting_car else None,
            "waitingCars": [car.to_dict() for car in self.waiting_cars],
        }

