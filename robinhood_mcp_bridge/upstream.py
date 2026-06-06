from __future__ import annotations

import json
from typing import Any

import httpx

from .auth import AuthRequiredError, OAuthManager
from .config import Settings


class UpstreamError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def parse_sse_json(text: str) -> dict[str, Any]:
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        return json.loads(payload)
    raise ValueError("SSE response did not contain a JSON data event")


class UpstreamMCPClient:
    def __init__(self, settings: Settings, auth: OAuthManager):
        self.settings = settings
        self.auth = auth
        self.last_status_code: int | None = None

    async def jsonrpc(
        self,
        *,
        method: str,
        params: dict[str, Any] | None = None,
        request_id: Any = None,
        tool_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id or f"bridge-{method}",
            "method": method,
        }
        if params is not None:
            body["params"] = params

        for attempt in range(2):
            token = await self.auth.ensure_access_token()
            headers = self._headers(token, method, params, tool_schema)
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as http:
                response = await http.post(self.settings.upstream_url, headers=headers, json=body)
            self.last_status_code = response.status_code
            if response.status_code == 401 and attempt == 0:
                await self.auth.refresh_token_from_state()
                continue
            if response.status_code >= 400:
                raise UpstreamError(
                    f"Upstream MCP returned HTTP {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                return parse_sse_json(response.text)
            return response.json()
        raise AuthRequiredError("Upstream token was rejected. Re-run `make bootstrap` or `rh-mcp auth`.")

    def _headers(
        self,
        token: str,
        method: str,
        params: dict[str, Any] | None,
        tool_schema: dict[str, Any] | None,
    ) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "MCP-Protocol-Version": self.settings.mcp_protocol_version,
            "Mcp-Method": method,
        }
        if method == "tools/call" and params:
            name = params.get("name")
            if isinstance(name, str):
                headers["Mcp-Name"] = name
            arguments = params.get("arguments")
            if isinstance(arguments, dict) and tool_schema:
                headers.update(extract_mcp_param_headers(tool_schema, arguments))
        return headers


def extract_mcp_param_headers(schema: dict[str, Any], arguments: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}

    def visit(schema_node: Any, value_node: Any) -> None:
        if not isinstance(schema_node, dict):
            return
        header_name = schema_node.get("x-mcp-header")
        if header_name and value_node is not None:
            if isinstance(value_node, (str, int, bool)):
                header_value = str(value_node)
                if "\r" not in header_value and "\n" not in header_value:
                    headers[f"Mcp-Param-{header_name}"] = header_value
        properties = schema_node.get("properties")
        if isinstance(properties, dict) and isinstance(value_node, dict):
            for key, child_schema in properties.items():
                if key in value_node:
                    visit(child_schema, value_node[key])

    visit(schema.get("inputSchema", schema), arguments)
    return headers
