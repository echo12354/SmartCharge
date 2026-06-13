"""统一时间入口：模拟模式走 sim_clock，否则使用系统时间。"""

from datetime import datetime

from utils.sim_clock import sim_clock


def now() -> datetime:
    return sim_clock.now()
