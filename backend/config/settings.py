"""系统运行参数。

这些值对应需求书中的充电桩数量、功率、等候区容量和充电桩队列长度。
"""

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
WAITING_QUEUE_CAPACITY = 6
# 单个用户可同时持有的未完成充电请求上限（对应多辆车场景）。
MAX_ACTIVE_REQUESTS_PER_USER = 10
# 充电桩队列长度 M：当前实现为 1 个充电位 + 1 个等待位。
PILE_QUEUE_CAPACITY = 2

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

