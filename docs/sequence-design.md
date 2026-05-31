# Sequence Design

This document gives suggested sequence diagram object order for each required system event.

The general sequence pattern is:

```text
Actor
-> Controller
-> Service
-> Model
-> Database or Storage
```

At this skeleton stage, the exact database calls are only design placeholders.

## E_chargingRequest()

```text
User
-> ChargingRequestController
-> QueueService
-> ChargingRequest
-> WaitingQueue
-> WaitingCar
-> SchedulingService
```

## Modify_Amount()

```text
User
-> ChargingRequestController
-> QueueService
-> ChargingRequest
-> WaitingCar
```

## Modify_Mode()

```text
User
-> ChargingRequestController
-> QueueService
-> ChargingRequest
-> WaitingQueue
-> WaitingCar
```

## Query_Car_State()

```text
User
-> ChargingRequestController
-> QueueService
-> ChargingSessionService
-> ChargingRequest / WaitingCar / ChargingSession
```

## Start_Charging()

```text
System or User
-> ChargingSessionController
-> SchedulingService
-> ChargingSessionService
-> PileManagementService
-> ChargingPile
-> ChargingSession
```

In normal automatic scheduling, the sequence may start from `SchedulingService` instead of a user controller:

```text
SchedulingService
-> PileQueue
-> ChargingSessionService
-> PileManagementService
-> ChargingPile
-> ChargingSession
```

## Query_Charging_State()

```text
User
-> ChargingSessionController
-> ChargingSessionService
-> ChargingSession
-> ChargingPile
```

## End_Charging()

```text
User
-> ChargingSessionController
-> SchedulingService
-> ChargingSessionService
-> PileManagementService
-> ChargingSession
-> BillingService
-> Bill
```

## Request_Bill()

```text
User
-> BillController
-> BillingService
-> Bill
-> ChargingSession
```

## Request_DetailedList()

```text
User
-> BillController
-> BillingService
-> Bill
-> ChargingSession
-> ChargingPile
```

## powerOn()

```text
Admin
-> PileController
-> PileManagementService
-> ChargingPile
-> FaultRecoveryService
-> FaultRecord
```

If power on triggers recovery dispatch:

```text
Admin
-> PileController
-> FaultRecoveryService
-> PileManagementService
-> SchedulingService
-> PileQueue
-> WaitingCar
```

## setParameters()

```text
Admin
-> PileController
-> PileManagementService
-> ChargingPile
```

## Start_ChargingPile()

```text
Admin
-> PileController
-> PileManagementService
-> ChargingPile
```

## powerOff()

```text
Admin
-> PileController
-> PileManagementService
-> ChargingPile
-> FaultRecoveryService
-> ChargingSessionService
-> BillingService
-> Bill
-> FaultRecord
```

## Query_PileState()

```text
Admin
-> PileController
-> PileManagementService
-> ChargingPile
-> PileQueue
```

## Query_QueueState()

```text
User or Admin
-> QueueController
-> QueueService
-> WaitingQueue
-> WaitingCar
-> SchedulingService
-> PileQueue
```

## Priority Dispatch

```text
Admin or System
-> FaultController
-> FaultRecoveryService
-> SchedulingService
-> PileQueue
-> WaitingCar
-> DispatchDecision
```

## Time Sequence Dispatch

```text
Admin or System
-> FaultController
-> FaultRecoveryService
-> SchedulingService
-> WaitingCar
-> PileQueue
-> DispatchDecision
```

## Fault Recovery Dispatch

```text
Admin
-> FaultController
-> FaultRecoveryService
-> PileManagementService
-> ChargingPile
-> SchedulingService
-> PileQueue
-> WaitingCar
-> FaultRecord
```

## Recommended Diagrams for Assignment

Suggested sequence diagrams:

1. charging request and queue number generation
2. automatic scheduling and start charging
3. end charging and bill generation
4. pile power off and fault recovery
5. query queue / pile state

## Original-Style API Compatibility Sequence

For routes implemented by `CompatibilityController`, the sequence is:

```text
Actor
-> CompatibilityController
-> redesigned Service
-> Model
```

Example:

```text
User
-> CompatibilityController (/api/charging/request)
-> QueueService
-> ChargingRequest
-> WaitingQueue
-> SchedulingService
-> PileQueue
-> ChargingSessionService
```
