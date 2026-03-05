from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_hash(record: dict[str, Any]) -> str:
    # stable, deterministic hash across runs for same record content
    items = sorted((k, str(v)) for k, v in record.items())
    payload = "|".join(f"{k}={v}" for k, v in items).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]
