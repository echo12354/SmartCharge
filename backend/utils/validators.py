"""Validation helpers used by controllers and services."""


def require_fields(payload: dict, *fields: str):
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        return False, f"Missing required field(s): {', '.join(missing)}"
    return True, ""


def normalize_charge_mode(value: str) -> str:
    if value in ("fast", "FAST", "快充模式", "快充"):
        return "fast"
    if value in ("slow", "SLOW", "慢充模式", "慢充"):
        return "slow"
    raise ValueError("charge mode must be fast/slow")

