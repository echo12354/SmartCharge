# 核心类与静态结构设计

## 1. 设计目标

本文整理 SmartCharge 后端的核心类、模块职责和静态关系，用于支持类图绘制、接口扩展、业务维护和测试用例设计。

## 2. 控制器类

| 类或模块 | 职责 |
|---|---|
| `AuthController` | 用户注册、登录和身份相关接口 |
| `ChargingRequestController` | 提交充电请求、修改电量、修改模式、查询车辆状态、取消请求 |
| `QueueController` | 查询用户队列和管理员队列状态 |
| `SchedulingController` | 查询调度状态，手动触发调度 |
| `ChargingSessionController` | 开始充电、查询充电状态、结束充电、查询会话列表 |
| `BillController` | 查询账单列表和账单详情 |
| `PileController` | 查询充电桩、上下电、启动、修改参数 |
| `FaultController` | 充电桩故障、恢复、优先级调度和时间顺序调度 |
| `CompatibilityController` | 提供兼容接口，并统一委托到现有服务层 |

## 3. 服务类

| 类 | 职责 |
|---|---|
| `UserService` | 用户注册、登录、角色校验和用户查询 |
| `QueueService` | 创建和修改充电请求，维护等待队列、排队编号、车辆位置和队列状态 |
| `SchedulingService` | 选择合适充电桩，维护充电桩队列，生成调度决策 |
| `ChargingSessionService` | 创建、开始、更新、中断和结束充电会话 |
| `BillingService` | 根据充电会话计算费用，生成和查询账单 |
| `PileManagementService` | 管理充电桩状态、参数、统计信息和可用性 |
| `FaultRecoveryService` | 处理充电桩故障、受影响车辆、恢复调度和故障记录 |

## 4. 模型类

### 4.1 `User`

表示系统用户。

主要属性：

- `user_id`：用户标识。
- `username`：用户名。
- `password_hash`：密码摘要。
- `role`：用户角色。

主要职责：

- 作为充电请求和账单的归属主体。
- 区分普通用户和管理员。

### 4.2 `ChargingRequest`

表示一次用户充电请求。

主要属性：

- `request_id`：请求标识。
- `user_id`：用户标识。
- `charge_mode`：充电模式，通常分为快充和慢充。
- `requested_amount`：请求充电电量。
- `status`：请求状态。
- `queue_number`：排队号码。
- `created_at`：创建时间。

主要职责：

- 描述车辆充电需求。
- 记录排队状态和调度状态。

### 4.3 `WaitingCar`

表示等待充电的车辆。

主要属性：

- `user_id`
- `request_id`
- `charge_mode`
- `requested_amount`
- `queue_number`
- `queue_position`
- `assigned_pile_id`
- `join_time`

主要职责：

- 作为等待区和充电桩队列中的调度单元。
- 保存车辆在队列中的位置和目标充电桩。

### 4.4 `WaitingQueue`

表示充电站等待区。

主要属性：

- `capacity`：等待区容量。
- `cars`：等待车辆集合。
- `fast_counter`：快充排队计数器。
- `slow_counter`：慢充排队计数器。

主要行为：

- 添加等待车辆。
- 移除等待车辆。
- 生成排队号码。
- 按充电模式查询车辆。

### 4.5 `PileQueue`

表示单个充电桩对应的队列。

主要属性：

- `pile_id`：充电桩标识。
- `charging_car`：当前充电车辆。
- `waiting_car`：桩前等待车辆。
- `capacity`：队列容量。

主要行为：

- 添加车辆。
- 移除车辆。
- 将等待车辆移动到充电位置。
- 查询剩余容量。

### 4.6 `ChargingPile`

表示充电桩设备。

主要属性：

- `pile_id`：充电桩标识。
- `pile_type`：充电桩类型。
- `power`：充电功率。
- `status`：运行状态。
- `is_enabled`：是否启用。
- `parameters`：运行参数。

主要行为：

- 上电。
- 下电。
- 启动。
- 停止。
- 修改参数。
- 标记故障。
- 从故障中恢复。

### 4.7 `ChargingSession`

表示一次正在进行或已经结束的充电过程。

主要属性：

- `session_id`
- `user_id`
- `pile_id`
- `target_amount`
- `current_amount`
- `status`
- `start_time`
- `end_time`

主要行为：

- 开始充电。
- 更新充电进度。
- 完成充电。
- 中断充电。
- 停止充电。

### 4.8 `Bill`

表示充电账单。

主要属性：

- `bill_id`
- `session_id`
- `user_id`
- `pile_id`
- `energy_amount`
- `charge_fee`
- `service_fee`
- `total_fee`
- `created_at`

主要行为：

- 计算充电费。
- 计算服务费。
- 计算总费用。

### 4.9 `DispatchDecision`

表示一次调度决策。

主要属性：

- `decision_id`
- `request_id`
- `selected_pile_id`
- `strategy`
- `reason`
- `created_at`

主要职责：

- 记录车辆被分配到某个充电桩的原因。
- 支持调度过程追踪和调试。

### 4.10 `FaultRecord`

表示一次充电桩故障和恢复记录。

主要属性：

- `fault_id`
- `pile_id`
- `reason`
- `fault_time`
- `recovery_time`
- `affected_car_ids`
- `status`

主要职责：

- 保存故障发生、影响范围和恢复结果。
- 支持故障恢复调度。

## 5. 静态关系

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

## 6. 状态枚举建议

### 6.1 充电请求状态

- `WAITING`：等待中。
- `QUEUED`：已进入充电桩队列。
- `CHARGING`：充电中。
- `FINISHED`：已完成。
- `CANCELLED`：已取消。

### 6.2 充电桩状态

- `AVAILABLE`：可用。
- `BUSY`：使用中。
- `OFFLINE`：已关闭。
- `FAULT`：故障。

### 6.3 充电会话状态

- `RUNNING`：进行中。
- `FINISHED`：已结束。
- `INTERRUPTED`：已中断。

## 7. UML 包划分

建议在 UML 类图中按以下包组织：

```text
controllers
services
models
database
config
utils
```

核心类图可重点展示 `ChargingRequest`、`WaitingCar`、`WaitingQueue`、`PileQueue`、`ChargingPile`、`ChargingSession`、`Bill`、`DispatchDecision`、`FaultRecord` 以及对应服务类。
