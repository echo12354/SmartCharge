# 动态结构设计参考

## 1. 文档目的

本文描述 SmartCharge 关键业务场景中的对象交互顺序，用于支持顺序图绘制、接口联调和测试设计。

通用调用模式如下：

```text
参与者
-> 控制器
-> 服务
-> 模型
-> 数据或状态存储
```

## 2. 用户提交充电请求

```text
用户
-> ChargingRequestController
-> QueueService
-> ChargingRequest
-> WaitingQueue
-> WaitingCar
-> SchedulingService
```

关键点：

- 请求需要包含充电模式和请求电量。
- 系统生成排队编号。
- 车辆默认进入等待区。
- 如果充电区有可用容量，可以继续触发调度。

## 3. 修改充电电量

```text
用户
-> ChargingRequestController
-> QueueService
-> ChargingRequest
-> WaitingCar
```

关键点：

- 仅允许对符合业务状态的请求进行修改。
- 修改后需要同步更新等待车辆中的目标电量。

## 4. 修改充电模式

```text
用户
-> ChargingRequestController
-> QueueService
-> ChargingRequest
-> WaitingQueue
-> WaitingCar
```

关键点：

- 修改模式后需要重新生成或调整排队信息。
- 车辆应进入对应模式的等待队列。

## 5. 查询车辆状态

```text
用户
-> ChargingRequestController
-> QueueService
-> ChargingSessionService
-> ChargingRequest / WaitingCar / ChargingSession
```

关键点：

- 等待区车辆返回排队位置。
- 充电区车辆返回充电桩和充电会话状态。

## 6. 自动调度并开始充电

```text
系统或管理员
-> SchedulingController
-> SchedulingService
-> PileQueue
-> ChargingSessionService
-> PileManagementService
-> ChargingPile
-> ChargingSession
```

在自动调度场景中，也可以由服务内部触发：

```text
SchedulingService
-> PileQueue
-> ChargingSessionService
-> PileManagementService
-> ChargingPile
-> ChargingSession
```

关键点：

- 快充请求分配到快充桩，慢充请求分配到慢充桩。
- 调度需要遵守队列顺序和充电桩可用状态。
- 充电桩队列满时不继续移入车辆。

## 7. 查询充电状态

```text
用户
-> ChargingSessionController
-> ChargingSessionService
-> ChargingSession
-> ChargingPile
```

关键点：

- 返回当前充电桩、目标电量、已充电量和会话状态。
- 管理员视角可以扩展为查询所有会话。

## 8. 结束充电并生成账单

```text
用户或系统
-> ChargingSessionController
-> SchedulingService
-> ChargingSessionService
-> PileManagementService
-> ChargingSession
-> BillingService
-> Bill
```

关键点：

- 结束充电时记录结束时间和实际电量。
- 计费服务根据充电电量、分时电价和服务费率计算费用。
- 生成账单后释放充电桩，并尝试调度下一辆车。

## 9. 查询账单

### 9.1 查询账单列表

```text
用户或管理员
-> BillController
-> BillingService
-> Bill
-> ChargingSession
```

### 9.2 查询账单详情

```text
用户或管理员
-> BillController
-> BillingService
-> Bill
-> ChargingSession
-> ChargingPile
```

关键点：

- 普通用户通常只查询自己的账单。
- 管理员可以按用户、充电桩或时间范围查看账单。

## 10. 充电桩上电

```text
管理员
-> PileController
-> PileManagementService
-> ChargingPile
-> FaultRecoveryService
-> FaultRecord
```

如果上电后触发恢复调度：

```text
管理员
-> PileController
-> FaultRecoveryService
-> PileManagementService
-> SchedulingService
-> PileQueue
-> WaitingCar
```

## 11. 设置充电桩参数

```text
管理员
-> PileController
-> PileManagementService
-> ChargingPile
```

关键点：

- 参数修改应集中在充电桩管理服务中处理。
- 修改后需要保证调度服务读取到新的桩状态或功率信息。

## 12. 启动充电桩

```text
管理员
-> PileController
-> PileManagementService
-> ChargingPile
```

## 13. 充电桩下电或故障

```text
管理员或系统监控
-> PileController / FaultController
-> FaultRecoveryService
-> ChargingSessionService
-> BillingService
-> PileManagementService
-> ChargingPile
-> ChargingSession
-> Bill
-> FaultRecord
```

关键点：

- 故障桩不能继续接收新的车辆。
- 正在充电的车辆需要被中断、结算或重新调度。
- 故障处理应留下可追踪记录。

## 14. 查询充电桩状态

```text
管理员
-> PileController
-> PileManagementService
-> ChargingPile
-> PileQueue
```

## 15. 查询队列状态

```text
用户或管理员
-> QueueController
-> QueueService
-> WaitingQueue
-> WaitingCar
-> SchedulingService
-> PileQueue
```

## 16. 故障恢复调度

### 16.1 优先级调度

```text
管理员或系统
-> FaultController
-> FaultRecoveryService
-> SchedulingService
-> PileQueue
-> WaitingCar
-> DispatchDecision
```

### 16.2 时间顺序调度

```text
管理员或系统
-> FaultController
-> FaultRecoveryService
-> SchedulingService
-> WaitingCar
-> PileQueue
-> DispatchDecision
```

### 16.3 恢复后重新调度

```text
管理员
-> FaultController
-> FaultRecoveryService
-> PileManagementService
-> ChargingPile
-> SchedulingService
-> PileQueue
-> WaitingCar
-> FaultRecord
```

## 17. 兼容接口调用顺序

兼容接口统一由 `CompatibilityController` 接收，再委托给现有服务层：

```text
参与者
-> CompatibilityController
-> QueueService / SchedulingService / ChargingSessionService / BillingService / PileManagementService
-> 模型对象
```

该设计可以让不同接口路径复用同一套业务逻辑。
