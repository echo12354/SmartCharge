# Charging Station

This is an independent redesign of the smart charging station scheduling and billing system.

It does not copy code from the existing project. It only follows the same business requirements:

- user charging requests
- waiting queue management
- charging pile management
- dispatching
- charging sessions
- billing
- fault handling and recovery

Current stage: first runnable Flask backend version with in-memory storage.

## Layered Structure

```text
backend/
├─ controllers/    Flask route controllers
├─ services/       business logic and system event handling
├─ models/         domain objects
├─ repositories/   data access classes
├─ database/       database connection and initialization
├─ config/         application configuration
└─ utils/          shared helper functions
```

Frontend is reserved for later development.

## Run Backend

```bash
cd charging-station-redesign/backend
pip install flask flask-cors
python app.py
```

The backend runs on:

```text
http://localhost:5001
```

Health check:

```text
GET /api/health
```

## Default Users

```text
admin / 123
user  / 123
test1 / 123
test2 / 123
```

## Main API Groups

Redesigned API:

```text
POST /api/auth/login
POST /api/auth/register

POST  /api/charging-requests
PATCH /api/charging-requests/amount
PATCH /api/charging-requests/mode
GET   /api/charging-requests/car-state
POST  /api/charging-requests/cancel

GET /api/queues/state
GET /api/queues/me

POST /api/scheduling/dispatch
GET  /api/scheduling/state

POST /api/charging-sessions/start
GET  /api/charging-sessions/state
POST /api/charging-sessions/{session_id}/end

GET /api/bills
GET /api/bills/{bill_id}

GET   /api/piles
GET   /api/piles/{pile_id}
POST  /api/piles/{pile_id}/power-on
POST  /api/piles/{pile_id}/power-off
POST  /api/piles/{pile_id}/start
PATCH /api/piles/{pile_id}/parameters

POST /api/faults/{pile_id}
POST /api/faults/{pile_id}/recover
POST /api/faults/{pile_id}/priority-dispatch
POST /api/faults/{pile_id}/time-sequence-dispatch
GET  /api/faults
```

Compatibility API:

The backend also provides original-style `/api/...` routes such as:

```text
POST /api/login
POST /api/register
POST /api/charging/request
GET  /api/charging/current
GET  /api/queue/status
POST /api/queue/modify-amount
POST /api/queue/modify-mode
GET  /api/admin/piles
POST /api/admin/piles/{pile_id}/status
GET  /api/dispatch/statistics
GET  /api/charging/records
```

These routes are implemented in `backend/controllers/compatibility_controller.py` and still call the redesigned services.

## Notes

- This version uses memory storage only.
- The `database/` directory is reserved for future persistence.
- The project intentionally uses `QueueService` for charging requests and waiting queue behavior. There is no `ChargingRequestService` and no `WaitingQueueService`.
