# System Events and Class Mapping

This document maps OOD system events to planned controllers, services, models, and repositories.

## User Charging Request Events

| System Event | Controller | Service | Main Models | Repository |
|---|---|---|---|---|
| `E_chargingRequest()` | `ChargingRequestController` | `QueueService` | `ChargingRequest`, `WaitingCar`, `WaitingQueue` | `ChargingRequestRepository`, `QueueRepository` |
| `Modify_Amount()` | `ChargingRequestController` | `QueueService` | `ChargingRequest`, `WaitingCar` | `ChargingRequestRepository`, `QueueRepository` |
| `Modify_Mode()` | `ChargingRequestController` | `QueueService` | `ChargingRequest`, `WaitingCar`, `WaitingQueue` | `ChargingRequestRepository`, `QueueRepository` |
| `Query_Car_State()` | `ChargingRequestController` | `QueueService`, `ChargingSessionService` | `ChargingRequest`, `WaitingCar`, `ChargingSession` | `ChargingRequestRepository`, `QueueRepository`, `ChargingSessionRepository` |

## Charging Session Events

| System Event | Controller | Service | Main Models | Repository |
|---|---|---|---|---|
| `Start_Charging()` | `ChargingSessionController` | `ChargingSessionService`, `ChargingPileService` | `ChargingSession`, `ChargingPile`, `ChargingPileQueue` | `ChargingSessionRepository`, `ChargingPileRepository` |
| `Query_Charging_State()` | `ChargingSessionController` | `ChargingSessionService` | `ChargingSession`, `ChargingPile` | `ChargingSessionRepository`, `ChargingPileRepository` |
| `End_Charging()` | `ChargingSessionController` | `ChargingSessionService`, `BillService`, `ChargingPileService` | `ChargingSession`, `ChargingBill`, `ChargingPile` | `ChargingSessionRepository`, `ChargingBillRepository`, `ChargingPileRepository` |

## Billing Events

| System Event | Controller | Service | Main Models | Repository |
|---|---|---|---|---|
| `Request_Bill()` | `BillController` | `BillService` | `ChargingBill`, `ChargingSession` | `ChargingBillRepository`, `ChargingSessionRepository` |
| `Request_DetailedList()` | `BillController` | `BillService` | `ChargingBill`, `ChargingSession`, `ChargingPile` | `ChargingBillRepository`, `ChargingSessionRepository`, `ChargingPileRepository` |

## Charging Pile Events

| System Event | Controller | Service | Main Models | Repository |
|---|---|---|---|---|
| `powerOn()` | `ChargingPileController` | `ChargingPileService`, `FaultService` | `ChargingPile`, `FaultRecord` | `ChargingPileRepository`, `FaultRecordRepository` |
| `setParameters()` | `ChargingPileController` | `ChargingPileService` | `ChargingPile` | `ChargingPileRepository` |
| `Start_ChargingPile()` | `ChargingPileController` | `ChargingPileService` | `ChargingPile` | `ChargingPileRepository` |
| `powerOff()` | `ChargingPileController` | `ChargingPileService`, `FaultService`, `ChargingSessionService`, `BillService` | `ChargingPile`, `ChargingSession`, `ChargingBill`, `FaultRecord` | `ChargingPileRepository`, `ChargingSessionRepository`, `ChargingBillRepository`, `FaultRecordRepository` |
| `Query_PileState()` | `ChargingPileController` | `ChargingPileService`, `QueueService` | `ChargingPile`, `ChargingPileQueue` | `ChargingPileRepository`, `QueueRepository` |
| `Query_QueueState()` | `QueueController` | `QueueService`, `DispatchService` | `WaitingQueue`, `WaitingCar`, `ChargingPileQueue` | `QueueRepository`, `ChargingPileRepository` |

## Dispatch and Fault Events

| System Event | Controller | Service | Main Models | Repository |
|---|---|---|---|---|
| `Priority Dispatch` | `FaultController` or internal service call | `FaultService`, `DispatchService` | `WaitingCar`, `ChargingPileQueue`, `DispatchDecision` | `QueueRepository`, `ChargingPileRepository` |
| `Time Sequence Dispatch` | `FaultController` or internal service call | `FaultService`, `DispatchService` | `WaitingCar`, `ChargingPileQueue`, `DispatchDecision` | `QueueRepository`, `ChargingPileRepository` |
| `Fault Recovery Dispatch` | `FaultController` | `FaultService`, `DispatchService`, `ChargingPileService` | `ChargingPile`, `WaitingCar`, `ChargingPileQueue`, `FaultRecord` | `ChargingPileRepository`, `QueueRepository`, `FaultRecordRepository` |

## Suggested Sequence Diagram Participants

For each event, use this general pattern:

```text
Actor
-> Controller
-> Service
-> Model
-> Repository
-> Database
```

For dispatch events:

```text
Admin or System
-> FaultController or DispatchController
-> FaultService
-> DispatchService
-> ChargingPileQueue
-> QueueRepository
-> ChargingPileRepository
```

For charging completion:

```text
User
-> ChargingSessionController
-> ChargingSessionService
-> ChargingPileService
-> BillService
-> ChargingBillRepository
```
