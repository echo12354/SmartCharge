"""参数校验工具。

用于 Controller 和 Service 入口处统一处理必填字段和充电模式转换。
"""


def require_fields(payload: dict, *fields: str):
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        return False, f"Missing required field(s): {', '.join(missing)}"
    return True, ""


def normalize_charge_mode(value: str) -> str:
    """把接口传入的快充/慢充描述统一转换为内部使用的 fast/slow。"""
    if value in ("fast", "FAST", "快充模式", "快充"):
        return "fast"
    if value in ("slow", "SLOW", "慢充模式", "慢充"):
        return "slow"
    raise ValueError("charge mode must be fast/slow")

