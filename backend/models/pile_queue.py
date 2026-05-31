"""Charging pile queue model."""

from dataclasses import dataclass

from config.settings import PILE_QUEUE_CAPACITY
from models.waiting_car import WaitingCar


@dataclass
class PileQueue:
    pile_id: str
    capacity: int = PILE_QUEUE_CAPACITY
    charging_car: WaitingCar | None = None
    waiting_car: WaitingCar | None = None

    def has_space(self) -> bool:
        return self.charging_car is None or self.waiting_car is None

    def is_empty(self) -> bool:
        return self.charging_car is None and self.waiting_car is None

    def add_car(self, car: WaitingCar) -> str:
        if self.charging_car is None:
            self.charging_car = car
            car.queue_position = "CHARGING"
        elif self.waiting_car is None:
            self.waiting_car = car
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
        if self.waiting_car and self.waiting_car.user_id == user_id:
            car = self.waiting_car
            self.waiting_car = None
            return car
        return None

    def promote_waiting_car(self) -> WaitingCar | None:
        if self.charging_car is None and self.waiting_car is not None:
            self.charging_car = self.waiting_car
            self.waiting_car = None
            self.charging_car.queue_position = "CHARGING"
            return self.charging_car
        return None

    def cars(self) -> list[WaitingCar]:
        return [car for car in (self.charging_car, self.waiting_car) if car]

    def to_dict(self):
        return {
            "pileId": self.pile_id,
            "capacity": self.capacity,
            "availableCapacity": int(self.charging_car is None) + int(self.waiting_car is None),
            "chargingCar": self.charging_car.to_dict() if self.charging_car else None,
            "waitingCar": self.waiting_car.to_dict() if self.waiting_car else None,
        }

