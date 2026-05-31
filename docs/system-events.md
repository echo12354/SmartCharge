# System Events Mapping

This document maps the required OOD system events to the redesigned controller, service, and model objects.

## Event Table

| System Event | Controller | Service | Main Model Objects |
|---|---|---|---|
| `E_chargingRequest()` | `controllers/charging_request_controller.py` | `services/queue_service.py` | `ChargingRequest`, `WaitingCar`, `WaitingQueue` |
| `Modify_Amount()` | `controllers/charging_request_controller.py` | `services/queue_service.py` | `ChargingRequest`, `WaitingCar` |
| `Modify_Mode()` | `controllers/charging_request_controller.py` | `services/queue_service.py` | `ChargingRequest`, `WaitingCar`, `WaitingQueue` |
| `Query_Car_State()` | `controllers/charging_request_controller.py` | `services/queue_service.py`, `services/charging_session_service.py` | `ChargingRequest`, `WaitingCar`, `ChargingSession` |
| `Start_Charging()` | `controllers/charging_session_controller.py` | `services/scheduling_service.py`, `services/charging_session_service.py`, `services/pile_management_service.py` | `ChargingSession`, `ChargingPile`, `PileQueue` |
| `Query_Charging_State()` | `controllers/charging_session_controller.py` | `services/charging_session_service.py` | `ChargingSession`, `ChargingPile` |
| `End_Charging()` | `controllers/charging_session_controller.py` | `services/scheduling_service.py`, `services/charging_session_service.py`, `services/billing_service.py` | `ChargingSession`, `Bill`, `ChargingPile` |
| `Request_Bill()` | `controllers/bill_controller.py` | `services/billing_service.py` | `Bill`, `ChargingSession` |
| `Request_DetailedList()` | `controllers/bill_controller.py` | `services/billing_service.py` | `Bill`, `ChargingSession`, `ChargingPile` |
| `powerOn()` | `controllers/pile_controller.py` | `services/fault_recovery_service.py`, `services/pile_management_service.py` | `ChargingPile`, `FaultRecord`, `PileQueue` |
| `setParameters()` | `controllers/pile_controller.py` | `services/pile_management_service.py` | `ChargingPile` |
| `Start_ChargingPile()` | `controllers/pile_controller.py` | `services/pile_management_service.py` | `ChargingPile` |
| `powerOff()` | `controllers/pile_controller.py` | `services/fault_recovery_service.py`, `services/charging_session_service.py`, `services/billing_service.py` | `ChargingPile`, `ChargingSession`, `Bill`, `FaultRecord` |
| `Query_PileState()` | `controllers/pile_controller.py` | `services/pile_management_service.py`, `services/scheduling_service.py` | `ChargingPile`, `PileQueue` |
| `Query_QueueState()` | `controllers/queue_controller.py` | `services/queue_service.py`, `services/scheduling_service.py` | `WaitingQueue`, `WaitingCar`, `PileQueue` |
| `Priority Dispatch` | `controllers/fault_controller.py` | `services/fault_recovery_service.py`, `services/scheduling_service.py` | `WaitingCar`, `PileQueue`, `DispatchDecision` |
| `Time Sequence Dispatch` | `controllers/fault_controller.py` | `services/fault_recovery_service.py`, `services/scheduling_service.py` | `WaitingCar`, `PileQueue`, `DispatchDecision` |
| `Fault Recovery Dispatch` | `controllers/fault_controller.py`, `controllers/pile_controller.py` | `services/fault_recovery_service.py`, `services/scheduling_service.py`, `services/pile_management_service.py` | `FaultRecord`, `ChargingPile`, `WaitingCar`, `PileQueue` |

## Original API Compatibility

The redesigned backend also includes `controllers/compatibility_controller.py`.

Its purpose is to preserve original-style API behavior while still using the redesigned service layer:

```text
compatibility_controller.py
-> QueueService
-> SchedulingService
-> ChargingSessionService
-> BillingService
-> PileManagementService
-> FaultRecoveryService
```

This keeps old routes such as `/api/charging/request`, `/api/queue/status`, `/api/admin/piles`, and `/api/dispatch/statistics` available without reintroducing the old monolithic `server.py` structure.

## Business Modules

### Charging Request Module

Events:

- `E_chargingRequest()`
- `Modify_Amount()`
- `Modify_Mode()`
- `Query_Car_State()`

Core objects:

- `ChargingRequestController`
- `QueueService`
- `ChargingRequest`
- `WaitingCar`
- `WaitingQueue`

### Queue and Scheduling Module

Events:

- `Query_QueueState()`
- `Priority Dispatch`
- `Time Sequence Dispatch`

Core objects:

- `QueueController`
- `SchedulingService`
- `QueueService`
- `WaitingQueue`
- `PileQueue`
- `DispatchDecision`

### Charging Session Module

Events:

- `Start_Charging()`
- `Query_Charging_State()`
- `End_Charging()`

Core objects:

- `ChargingSessionController`
- `ChargingSessionService`
- `PileManagementService`
- `ChargingSession`
- `ChargingPile`

### Billing Module

Events:

- `Request_Bill()`
- `Request_DetailedList()`

Core objects:

- `BillController`
- `BillingService`
- `Bill`
- `ChargingSession`

### Charging Pile and Fault Module

Events:

- `powerOn()`
- `setParameters()`
- `Start_ChargingPile()`
- `powerOff()`
- `Query_PileState()`
- `Fault Recovery Dispatch`

Core objects:

- `PileController`
- `FaultController`
- `PileManagementService`
- `FaultRecoveryService`
- `ChargingPile`
- `FaultRecord`
