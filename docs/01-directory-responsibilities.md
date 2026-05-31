# Directory Responsibilities

The redesign uses a simple layered architecture suitable for a software engineering OOD assignment.

## backend/controllers

Controller layer.

Responsibilities:

- define Flask routes
- receive HTTP requests
- parse path parameters, query parameters, headers, and JSON bodies
- call service methods
- return JSON responses
- avoid business logic
- avoid direct database access

Planned controller files:

- `auth_controller.py`
- `charging_request_controller.py`
- `queue_controller.py`
- `charging_session_controller.py`
- `bill_controller.py`
- `charging_pile_controller.py`
- `dispatch_controller.py`
- `fault_controller.py`

## backend/services

Business logic layer.

Responsibilities:

- implement system events
- coordinate models and repositories
- enforce charging, queue, dispatch, billing, and fault rules
- keep controllers thin

Planned service classes:

- `UserService`
- `QueueService`
- `ChargingSessionService`
- `BillService`
- `ChargingPileService`
- `DispatchService`
- `FaultService`

## backend/models

Domain object layer.

Responsibilities:

- represent system entities
- hold object state
- provide simple domain behavior and state transitions
- support UML class diagram design

Planned model classes:

- `User`
- `ChargingRequest`
- `WaitingCar`
- `WaitingQueue`
- `ChargingPile`
- `ChargingPileQueue`
- `ChargingSession`
- `ChargingBill`
- `DispatchDecision`
- `FaultRecord`

## backend/repositories

Data access layer.

Responsibilities:

- read and write model data
- hide SQL or storage details from services
- provide CRUD-style methods
- keep services independent from database implementation details

Planned repository classes:

- `UserRepository`
- `ChargingRequestRepository`
- `QueueRepository`
- `ChargingPileRepository`
- `ChargingSessionRepository`
- `ChargingBillRepository`
- `FaultRecordRepository`

## backend/database

Database initialization and connection layer.

Responsibilities:

- create database connection
- initialize tables
- seed initial charging pile and default user data
- provide transaction/session utilities if needed

## backend/config

Configuration layer.

Responsibilities:

- Flask settings
- database settings
- charging pile count and power settings
- queue capacity settings
- pricing settings
- dispatch settings

## backend/utils

Utility layer.

Responsibilities:

- response helpers
- validators
- time formatting
- ID generation
- common exception classes

## frontend

Reserved frontend directory.

The first backend version may only expose APIs. A simple frontend can be added later.
