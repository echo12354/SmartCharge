# SmartCharge

SmartCharge 是一个新能源汽车充电调度与计费管理系统，用于模拟充电站中的用户充电请求、排队调度、充电桩管理、充电过程记录、账单生成和故障恢复等业务流程。

项目后端基于 Flask 和 Python 实现，代码按前后端分离思路组织。当前工作区以后端 API 和系统设计文档为主，`frontend` 目录作为前端扩展入口保留。

## 技术栈

- 后端框架：Flask
- 编程语言：Python
- 接口形式：HTTP JSON API
- 架构方式：前后端分离结构
- 业务组织：控制器、服务层、领域模型、配置与工具模块分层

## 主要功能

- 用户注册、登录和角色区分。
- 用户提交快充或慢充请求，并获得排队编号。
- 支持修改充电电量、修改充电模式、取消充电请求。
- 维护等待区队列和各充电桩队列。
- 根据充电模式、队列顺序和充电桩状态执行调度。
- 管理充电桩启停、上下电、参数调整、故障和恢复。
- 记录充电会话状态，支持开始充电、查询状态和结束充电。
- 根据充电电量和计费规则生成账单。
- 提供兼容接口，便于使用不同测试入口验证业务流程。

## 项目结构

```text
SmartCharge/
|-- README.md
|-- backend/
|   |-- app.py
|   |-- config/
|   |-- controllers/
|   |-- database/
|   |-- models/
|   |-- services/
|   `-- utils/
|-- docs/
|   |-- architecture.md
|   |-- class-design.md
|   |-- sequence-design.md
|   `-- system-events.md
`-- frontend/
```

主要目录说明：

- `backend/app.py`：Flask 应用入口，注册各业务蓝图。
- `backend/controllers/`：接口控制器，负责接收请求、解析参数并返回 JSON 响应。
- `backend/services/`：业务服务层，负责排队、调度、充电、计费和故障恢复逻辑。
- `backend/models/`：领域模型，描述用户、充电请求、队列、充电桩、会话和账单等对象。
- `backend/config/`：系统参数配置，例如充电桩数量、功率、队列容量和计费单价。
- `backend/database/`：数据库连接与初始化预留模块，当前用于描述数据状态。
- `backend/utils/`：响应封装、参数校验、编号生成等通用工具。
- `docs/`：系统架构、类设计、动态结构和系统事件映射文档。
- `frontend/`：前端项目预留目录。

## 后端运行方法

进入后端目录：

```bash
cd backend
```

安装运行依赖：

```bash
pip install flask flask-cors
```

启动后端服务：

```bash
python app.py
```

默认服务地址：

```text
http://localhost:5001
```

健康检查接口：

```text
GET /api/health
```

默认用户：

```text
admin / 123
user  / 123
test1 / 123
test2 / 123
```

## 接口测试说明

可以使用 Postman、Apifox、curl 或其他 HTTP 客户端进行接口测试。建议按以下顺序验证：

1. 调用健康检查接口确认服务已启动。
2. 使用默认用户登录，或注册新用户。
3. 提交充电请求并查看排队状态。
4. 触发调度，查看车辆是否进入充电桩队列。
5. 开始充电并查询充电会话状态。
6. 结束充电并查询账单。
7. 测试充电桩上下电、故障和恢复场景。

常用接口分组：

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

示例：

```bash
curl http://localhost:5001/api/health
```

## 文档说明

- `docs/architecture.md`：系统架构设计。
- `docs/class-design.md`：核心类与静态结构设计。
- `docs/sequence-design.md`：动态结构设计参考。
- `docs/system-events.md`：系统事件与代码映射。
