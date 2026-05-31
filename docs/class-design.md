# Class Design

This document lists the core classes and relationships for UML class diagrams.

## Controller Classes

| Class | Responsibility |
|---|---|
| `AuthController` | login, register, current user query |
| `ChargingRequestController` | submit charging request, modify request, query car state |
| `QueueController` | query user queue and admin queue state |
| `SchedulingController` | query scheduling state and optionally trigger scheduling |
| `ChargingSessionController` | start, query, and end charging sessions |
| `BillController` | bill and detailed list queries |
| `PileController` | pile power, parameters, state, and detail operations |
| `FaultController` | pile fault, recovery, and recovery dispatch operations |
| `CompatibilityController` | original-style API route compatibility, delegating to redesigned services |

## Service Classes

| Class | Responsibility |
|---|---|
| `UserService` | user registration, login, role validation |
| `QueueService` | charging request creation/modification, waiting queue, queue number, car position, and queue state |
| `SchedulingService` | select charging pile and manage pile queues |
| `ChargingSessionService` | create, start, update, and stop charging sessions |
| `BillingService` | calculate and query bills |
| `PileManagementService` | manage pile state, pile parameters, and pile statistics |
| `FaultRecoveryService` | handle pile faults, affected cars, and recovery dispatch |

## Model Classes

### User

Represents a registered system user.

Important attributes:

- `user_id`
- `username`
- `password_hash`
- `role`

### ChargingRequest

Represents a user's charging request.

Important attributes:

- `request_id`
- `user_id`
- `charge_mode`
- `requested_amount`
- `status`
- `queue_number`
- `created_at`

### WaitingCar

Represents a car waiting for charging.

Important attributes:

- `user_id`
- `request_id`
- `charge_mode`
- `requested_amount`
- `queue_number`
- `queue_position`
- `assigned_pile_id`
- `join_time`

### WaitingQueue

Represents the station waiting area.

Important attributes:

- `capacity`
- `cars`
- `fast_counter`
- `slow_counter`

Important behavior:

- add waiting car
- remove waiting car
- generate queue number
- query cars by mode

### PileQueue

Represents the two-slot queue of one charging pile.

Important attributes:

- `pile_id`
- `charging_car`
- `waiting_car`
- `capacity`

Important behavior:

- add car
- remove car
- move waiting car to charging slot
- query available capacity

### ChargingPile

Represents a charging pile.

Important attributes:

- `pile_id`
- `pile_type`
- `power`
- `status`
- `is_enabled`
- `parameters`

Important behavior:

- power on
- power off
- start pile
- stop pile
- update parameters
- mark fault
- recover from fault

### ChargingSession

Represents an active or historical charging process.

Important attributes:

- `session_id`
- `user_id`
- `pile_id`
- `target_amount`
- `current_amount`
- `status`
- `start_time`
- `end_time`

Important behavior:

- start
- update progress
- complete
- interrupt
- stop

### Bill

Represents a charging bill or detailed list item.

Important attributes:

- `bill_id`
- `session_id`
- `user_id`
- `pile_id`
- `energy_amount`
- `charge_fee`
- `service_fee`
- `total_fee`
- `created_at`

Important behavior:

- calculate charge fee
- calculate service fee
- calculate total fee

### DispatchDecision

Represents one scheduling decision.

Important attributes:

- `decision_id`
- `request_id`
- `selected_pile_id`
- `strategy`
- `reason`
- `created_at`

### FaultRecord

Represents one charging pile fault and recovery record.

Important attributes:

- `fault_id`
- `pile_id`
- `reason`
- `fault_time`
- `recovery_time`
- `affected_car_ids`
- `status`

## UML Relationships

```text
User 1 ---- 0..* ChargingRequest
ChargingRequest 1 ---- 0..1 WaitingCar
WaitingQueue 1 ---- 0..* WaitingCar
ChargingPile 1 ---- 1 PileQueue
PileQueue 1 ---- 0..2 WaitingCar
ChargingPile 1 ---- 0..* ChargingSession
ChargingSession 1 ---- 0..1 Bill
SchedulingService 1 ---- 0..* DispatchDecision
FaultRecoveryService 1 ---- 0..* FaultRecord
FaultRecord 1 ---- 0..* WaitingCar
```

## Suggested UML Packages

```text
controllers
services
models
database
config
utils
```

For the second software engineering assignment, the most useful class diagram can focus on:

- `ChargingRequest`
- `WaitingCar`
- `WaitingQueue`
- `PileQueue`
- `ChargingPile`
- `ChargingSession`
- `Bill`
- `DispatchDecision`
- `FaultRecord`
- corresponding service classes

## Implemented Code Files

```text
models/user.py
models/charging_request.py
models/waiting_car.py
models/waiting_queue.py
models/pile_queue.py
models/charging_pile.py
models/charging_session.py
models/bill.py
models/dispatch_decision.py
models/fault_record.py

services/user_service.py
services/queue_service.py
services/scheduling_service.py
services/charging_session_service.py
services/billing_service.py
services/pile_management_service.py
services/fault_recovery_service.py
controllers/compatibility_controller.py
```
