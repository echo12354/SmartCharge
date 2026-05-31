"""Application settings for the redesigned charging station backend."""

FAST_PILES = ("A", "B")
SLOW_PILES = ("C", "D", "E")

PILE_POWER = {
    "A": 30.0,
    "B": 30.0,
    "C": 7.0,
    "D": 7.0,
    "E": 7.0,
}

WAITING_QUEUE_CAPACITY = 6
PILE_QUEUE_CAPACITY = 2

SERVICE_FEE_RATE = 0.8
PEAK_PRICE = 1.0
NORMAL_PRICE = 0.7
VALLEY_PRICE = 0.4

DEFAULT_USERS = [
    {"username": "admin", "password": "123", "role": "admin"},
    {"username": "user", "password": "123", "role": "user"},
    {"username": "test1", "password": "123", "role": "user"},
    {"username": "test2", "password": "123", "role": "user"},
]

