"""Small ID helpers."""

from datetime import datetime
from uuid import uuid4


def generate_id(prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{suffix}"

