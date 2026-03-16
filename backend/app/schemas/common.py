from datetime import datetime
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def utc_now() -> datetime:
    return datetime.utcnow()
