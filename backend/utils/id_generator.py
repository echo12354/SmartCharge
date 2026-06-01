"""业务编号生成工具。

为请求、会话、账单、故障和调度决策生成带业务前缀的唯一编号。
"""

from datetime import datetime
from uuid import uuid4


def generate_id(prefix: str) -> str:
    """使用时间戳和随机后缀生成便于识别的业务 ID。"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{suffix}"

