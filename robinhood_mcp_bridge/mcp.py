from __future__ import annotations

import json
from typing import Any


JSONRPC_VERSION = "2.0"


def jsonrpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def jsonrpc_error(
    request_id: Any,
    code: int,
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def tool_text_result(
    text: str,
    *,
    is_error: bool = False,
    structured: Any | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }
    if structured is not None:
        result["structuredContent"] = structured
    return result


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def is_tool_error_response(response: dict[str, Any]) -> bool:
    if "error" in response:
        return True
    result = response.get("result")
    return isinstance(result, dict) and result.get("isError") is True
