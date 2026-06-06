from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SENSITIVE_KEY_PARTS = {
    "authorization",
    "access_token",
    "refresh_token",
    "client_secret",
    "password",
    "signature",
    "api_key",
}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def mask_account(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"***{value[-4:]}"


def sanitize(value: Any, key: str | None = None) -> Any:
    key_lower = (key or "").lower()
    if any(part in key_lower for part in SENSITIVE_KEY_PARTS):
        return "***REDACTED***"
    if "account" in key_lower and isinstance(value, str):
        return mask_account(value)
    if isinstance(value, dict):
        return {str(k): sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(item, key) for item in value]
    return value


def find_order_ids(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).lower()
            if key_lower in {"order_id", "orderid"} and isinstance(item, str):
                found.append(item)
            elif key_lower == "id" and isinstance(item, str) and "-" in item:
                found.append(item)
            else:
                found.extend(find_order_ids(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_order_ids(item))
    return sorted(set(found))


class AuditLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log_tool_call(
        self,
        *,
        request_id: str,
        client_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        decision: str,
        upstream_status: int | None = None,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        event = {
            "ts": datetime.now(UTC).isoformat(),
            "request_id": request_id,
            "client_id_hash": stable_hash(client_id),
            "tool_name": tool_name,
            "arguments": sanitize(arguments),
            "decision": decision,
            "upstream_status": upstream_status,
            "order_ids": find_order_ids(result),
            "error": error,
        }
        line = json.dumps(event, sort_keys=True, separators=(",", ":"))
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.write("\n")
