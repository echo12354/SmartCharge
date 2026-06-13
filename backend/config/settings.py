"""系统运行参数。

这些值对应需求书中的充电桩数量、功率、等候区容量和充电桩队列长度。
"""

from datetime import datetime

# 需求书约定：A、B 为快充桩。
FAST_PILES = ("A", "B")
# 需求书约定：C、D、E 为慢充桩。
SLOW_PILES = ("C", "D", "E")

# 充电功率单位为“度/小时”：快充 30，慢充 10。
PILE_POWER = {
    "A": 30.0,
    "B": 30.0,
    "C": 10.0,
    "D": 10.0,
    "E": 10.0,
}

# 等候区容量 N：车辆提交请求后，先进入等候区等待叫号。
WAITING_QUEUE_CAPACITY = 10
# 单个用户可同时持有的未完成充电请求上限（对应多辆车场景）。
MAX_ACTIVE_REQUESTS_PER_USER = 30
# 充电桩排队队列长度 M：1 个充电位 + (M-1) 个等待位。
PILE_QUEUE_CAPACITY = 3

# 验收测试模拟时钟（作业验收用例.xlsx 比例尺 1:10，6:00 起算）。
SIMULATION_ENABLED = False
SIMULATION_START_TIME = datetime(2026, 6, 3, 6, 0, 0)
SIMULATION_MINUTES_PER_EVENT = 5
SIMULATION_TIME_SCALE = 10
# 桩编号与验收表列名映射：F1/F2=快充1/2，T1/T2/T3=慢充1/2/3。
ACCEPTANCE_FAST_PILE_ALIAS = {"F1": "A", "F2": "B"}
ACCEPTANCE_SLOW_PILE_ALIAS = {"T1": "C", "T2": "D", "T3": "E"}

# 计费参数：服务费固定按电量收取，电费按峰平谷时段确定单价。
SERVICE_FEE_RATE = 0.8
PEAK_PRICE = 1.0
NORMAL_PRICE = 0.7
VALLEY_PRICE = 0.4

DEFAULT_USERS = [
    {"username": "admin", "password": "123", "role": "admin"},
    {"username": "user", "password": "123", "role": "user"},
    {"username": "test1", "password": "123", "role": "user"},
    {"username": "test2", "password": "123", "role": "user"},
]

