# Core Class List

This document lists the classes planned for the redesigned OOD structure.

## Controllers

| Class / Module | Responsibility |
|---|---|
| `AuthController` | login, register, current user query |
| `ChargingRequestController` | submit request, modify amount, modify mode, query car state |
| `QueueController` | query user queue and admin queue state |
| `ChargingSessionController` | start charging, query charging state, end charging |
| `BillController` | query bill and detailed bill list |
| `ChargingPileController` | power on/off, start pile, set parameters, query pile state |
| `DispatchController` | expose dispatch-related operations if needed |
| `FaultController` | fault and recovery operations |

## Services

| Class | Responsibility |
|---|---|
| `UserService` | user registration, login, role query |
| `QueueService` | create/modify charging requests and manage waiting queue state |
| `QueueService` | manage waiting queue and pile queue state |
| `DispatchService` | select charging pile and perform scheduling |
| `ChargingPileService` | manage charging pile lifecycle and state |
| `ChargingSessionService` | create, start, update, and end charging sessions |
| `BillService` | calculate and query bills |
| `FaultService` | handle pile fault, priority dispatch, time sequence dispatch, recovery dispatch |

## Models

| Class | Main Attributes |
|---|---|
| `User` | `user_id`, `username`, `password_hash`, `role` |
| `ChargingRequest` | `request_id`, `user_id`, `mode`, `amount`, `status`, `queue_number` |
| `WaitingCar` | `user_id`, `request_id`, `mode`, `amount`, `queue_number`, `join_time` |
| `WaitingQueue` | `capacity`, `cars`, `fast_counter`, `slow_counter` |
| `ChargingPile` | `pile_id`, `pile_type`, `power`, `status`, `parameters` |
| `ChargingPileQueue` | `pile_id`, `charging_car`, `waiting_car`, `capacity` |
| `ChargingSession` | `session_id`, `user_id`, `pile_id`, `target_amount`, `current_amount`, `status` |
| `ChargingBill` | `bill_id`, `session_id`, `energy`, `charge_fee`, `service_fee`, `total_fee` |
| `DispatchDecision` | `decision_id`, `request_id`, `selected_pile_id`, `reason`, `created_at` |
| `FaultRecord` | `fault_id`, `pile_id`, `reason`, `fault_time`, `recovery_time`, `affected_cars` |

## Repositories

| Class | Responsibility |
|---|---|
| `UserRepository` | persist and query users |
| `ChargingRequestRepository` | persist and query charging requests |
| `QueueRepository` | persist and query queue entries |
| `ChargingPileRepository` | persist and query charging piles |
| `ChargingSessionRepository` | persist and query charging sessions |
| `ChargingBillRepository` | persist and query bills |
| `FaultRecordRepository` | persist and query fault records |

## Important Relationships for UML

```text
User 1 ---- 0..* ChargingRequest
ChargingRequest 1 ---- 0..1 WaitingCar
WaitingQueue 1 ---- 0..* WaitingCar
ChargingPile 1 ---- 1 ChargingPileQueue
ChargingPileQueue 1 ---- 0..2 WaitingCar
ChargingPile 1 ---- 0..* ChargingSession
ChargingSession 1 ---- 0..1 ChargingBill
DispatchService ---- DispatchDecision
FaultService ---- FaultRecord
```
