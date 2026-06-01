# 系统事件与代码映射

## 1. 文档目的

本文将 SmartCharge 的系统事件映射到当前后端代码中的控制器、服务类和主要模型对象，便于进行需求追踪、顺序图绘制、测试用例设计和代码定位。

## 2. 系统事件总表

| 系统事件 | 控制器 | 服务 | 主要模型对象 |
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

## 3. 用户充电请求模块

相关事件：

- `E_chargingRequest()`
- `Modify_Amount()`
- `Modify_Mode()`
- `Query_Car_State()`

核心代码：

- `ChargingRequestController`
- `QueueService`
- `ChargingRequest`
- `WaitingCar`
- `WaitingQueue`
- `ChargingSessionService`

主要说明：

- 充电请求由控制器接收，实际创建和修改逻辑集中在 `QueueService`。
- 等待区车辆由 `WaitingCar` 表示。
- 查询车辆状态时，需要同时检查等待队列和充电会话。

## 4. 队列与调度模块

相关事件：

- `Query_QueueState()`
- `Priority Dispatch`
- `Time Sequence Dispatch`
- `Fault Recovery Dispatch`

核心代码：

- `QueueController`
- `SchedulingController`
- `FaultController`
- `QueueService`
- `SchedulingService`
- `FaultRecoveryService`
- `WaitingQueue`
- `PileQueue`
- `DispatchDecision`

主要说明：

- `QueueService` 负责等待区状态和用户队列视图。
- `SchedulingService` 负责把等待车辆分配到合适的充电桩队列。
- `FaultRecoveryService` 在故障场景下协调受影响车辆的重新调度。

## 5. 充电会话模块

相关事件：

- `Start_Charging()`
- `Query_Charging_State()`
- `End_Charging()`

核心代码：

- `ChargingSessionController`
- `ChargingSessionService`
- `SchedulingService`
- `PileManagementService`
- `ChargingSession`
- `ChargingPile`

主要说明：

- 开始充电需要确认充电桩状态和车辆分配关系。
- 查询状态主要读取 `ChargingSession` 和 `ChargingPile`。
- 结束充电后需要释放充电桩，并触发账单生成和后续调度。

## 6. 账单模块

相关事件：

- `Request_Bill()`
- `Request_DetailedList()`

核心代码：

- `BillController`
- `BillingService`
- `Bill`
- `ChargingSession`

主要说明：

- `BillingService` 负责计费规则和账单查询。
- 账单数据来自充电会话中的电量、时间和充电桩信息。

## 7. 充电桩与故障模块

相关事件：

- `powerOn()`
- `setParameters()`
- `Start_ChargingPile()`
- `powerOff()`
- `Query_PileState()`
- `Fault Recovery Dispatch`

核心代码：

- `PileController`
- `FaultController`
- `PileManagementService`
- `FaultRecoveryService`
- `ChargingPile`
- `FaultRecord`
- `PileQueue`

主要说明：

- 充电桩状态变更由 `PileManagementService` 统一管理。
- 故障发生和恢复由 `FaultRecoveryService` 记录并协调调度。
- 充电桩状态查询需要同时展示设备状态和队列状态。

## 8. 兼容接口映射

当前后端还提供 `controllers/compatibility_controller.py`，用于接收兼容路径的请求。兼容接口不会单独维护业务逻辑，而是继续委托到现有服务层。

调用关系：

```text
CompatibilityController
-> QueueService
-> SchedulingService
-> ChargingSessionService
-> BillingService
-> PileManagementService
-> FaultRecoveryService
```

常见兼容接口包括：

- `POST /api/login`
- `POST /api/register`
- `POST /api/charging/request`
- `GET /api/charging/current`
- `GET /api/queue/status`
- `POST /api/queue/modify-amount`
- `POST /api/queue/modify-mode`
- `GET /api/admin/piles`
- `POST /api/admin/piles/{pile_id}/status`
- `GET /api/dispatch/statistics`
- `GET /api/charging/records`

## 9. 测试用例覆盖建议

建议按系统事件组织接口测试：

- 用户注册和登录。
- 创建充电请求并检查排队编号。
- 修改电量和修改充电模式。
- 查询车辆状态和队列状态。
- 手动触发调度并查询调度结果。
- 开始充电、查询充电状态、结束充电。
- 查询账单列表和账单详情。
- 模拟充电桩下电、故障、恢复和重新调度。
