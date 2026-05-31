# Implementation Order

The project should be implemented in small phases so each phase supports OOD diagrams and testing.

## Phase 1: Project Skeleton

Create Flask backend skeleton:

- app startup file
- blueprint registration
- config loader
- response helper
- empty controller modules
- empty service modules
- empty model modules
- empty repository modules

No complete business logic yet.

## Phase 2: Core Models

Implement model classes first:

1. `User`
2. `ChargingPile`
3. `ChargingRequest`
4. `WaitingCar`
5. `WaitingQueue`
6. `ChargingPileQueue`
7. `ChargingSession`
8. `ChargingBill`
9. `DispatchDecision`
10. `FaultRecord`

Reason: UML class diagrams are easiest to stabilize after model attributes and relationships are clear.

## Phase 3: Repository Interfaces and Simple Storage

Implement repositories with simple in-memory storage first:

1. `UserRepository`
2. `ChargingPileRepository`
3. `ChargingRequestRepository`
4. `QueueRepository`
5. `ChargingSessionRepository`
6. `ChargingBillRepository`
7. `FaultRecordRepository`

Reason: services can be tested without committing to a database schema too early.

## Phase 4: Basic User and Pile Services

Implement:

1. `UserService`
2. `ChargingPileService`

Reason: user and pile data are needed by later request, dispatch, and charging flows.

## Phase 5: Request and Queue Services

Implement:

1. `QueueService`

Supported events:

- `E_chargingRequest()`
- `Modify_Amount()`
- `Modify_Mode()`
- `Query_Car_State()`
- `Query_QueueState()`

## Phase 6: Dispatch Service

Implement:

1. `DispatchService`
2. shortest completion time selection
3. pile queue assignment

Supported events:

- normal dispatch after charging request
- `Priority Dispatch`
- `Time Sequence Dispatch`

## Phase 7: Charging Session and Billing

Implement:

1. `ChargingSessionService`
2. `BillService`

Supported events:

- `Start_Charging()`
- `Query_Charging_State()`
- `End_Charging()`
- `Request_Bill()`
- `Request_DetailedList()`

## Phase 8: Fault Handling and Recovery

Implement:

1. `FaultService`
2. fault queue handling
3. priority dispatch
4. time sequence dispatch
5. recovery dispatch

Supported events:

- `powerOff()`
- `powerOn()`
- `Fault Recovery Dispatch`

## Phase 9: Database Persistence

Replace or complement in-memory repositories with database-backed repositories.

Suggested tables:

- users
- charging_piles
- charging_requests
- queue_entries
- charging_sessions
- charging_bills
- dispatch_decisions
- fault_records

## Phase 10: Minimal Frontend

Add a simple frontend only after backend APIs are stable.

Initial pages:

- login
- submit charging request
- queue status
- charging status
- bill list
- admin pile dashboard
