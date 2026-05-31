# Architecture

This project is an independent redesign of the smart charging station scheduling and billing system. It references the business requirements and workflow of the existing system, but it does not copy its code.

The backend uses Flask and follows a simple layered architecture suitable for software engineering OOD coursework.

## Directory Structure

```text
charging-station-redesign/
├─ backend/
│  ├─ app.py
│  ├─ controllers/
│  ├─ services/
│  ├─ models/
│  ├─ database/
│  ├─ config/
│  └─ utils/
├─ frontend/
└─ docs/
```

## Layer Responsibilities

### controllers

The controller layer receives HTTP requests and returns HTTP responses.

Responsibilities:

- define Flask routes
- parse request body, query parameters, path parameters, and headers
- call service methods
- convert service results into JSON responses
- avoid business logic
- avoid direct database access

Typical files:

- `auth_controller.py`
- `charging_request_controller.py`
- `queue_controller.py`
- `charging_session_controller.py`
- `bill_controller.py`
- `pile_controller.py`
- `fault_controller.py`
- `scheduling_controller.py`

### services

The service layer implements system events and business workflows.

Responsibilities:

- validate business conditions
- coordinate multiple model objects
- coordinate queue, scheduling, pile, charging session, billing, and fault recovery
- call database access functions when persistence is needed

Typical classes:

- `UserService`
- `QueueService`
- `SchedulingService`
- `ChargingSessionService`
- `BillingService`
- `PileManagementService`
- `FaultRecoveryService`

### models

The model layer defines domain objects used in UML class diagrams.

Responsibilities:

- hold domain state
- expose simple state-changing methods
- describe relationships between charging requests, queues, piles, sessions, and bills

Typical classes:

- `User`
- `ChargingRequest`
- `WaitingCar`
- `WaitingQueue`
- `PileQueue`
- `ChargingPile`
- `ChargingSession`
- `Bill`
- `DispatchDecision`
- `FaultRecord`

### database

The database layer is responsible for database connection and initialization.

Responsibilities:

- create database connection
- initialize tables
- seed default users and charging piles
- provide simple persistence utilities for services

### config

Configuration layer.

Responsibilities:

- Flask settings
- database path or URL
- charging pile count
- charging pile power
- queue capacity
- pricing parameters
- scheduling parameters

### utils

Shared utilities.

Responsibilities:

- response formatting
- parameter validation
- ID generation
- time formatting
- common constants

## OOD View

For UML purposes, the system can be viewed as:

```text
Actor
-> Controller
-> Service
-> Model
-> Database
```

Controller objects are boundary/control entry points for API requests. Service objects are control objects for business use cases. Model objects are entity objects.
