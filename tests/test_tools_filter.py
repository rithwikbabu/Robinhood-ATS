from __future__ import annotations

import json

import pytest

from robinhood_mcp_bridge.config import Settings
from robinhood_mcp_bridge.server import BridgeService
from robinhood_mcp_bridge.tools import ALLOWED_TOOLS


ALL_TOOL_SCHEMAS = [{"name": name, "inputSchema": {"type": "object"}} for name in ALLOWED_TOOLS]


class FakeUpstream:
    last_status_code = 200

    def __init__(self, tools=None, result=None):
        self.tools = tools or ALL_TOOL_SCHEMAS
        self.result = result or {
            "content": [{"type": "text", "text": "{}"}],
            "structuredContent": {"ok": True},
        }
        self.calls = []

    async def jsonrpc(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["method"] == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": "1",
                "result": {"tools": self.tools},
            }
        return {
            "jsonrpc": "2.0",
            "id": "2",
            "result": self.result,
        }


def settings(tmp_path):
    return Settings(
        upstream_url="https://example.com/mcp",
        host="127.0.0.1",
        port=8080,
        mcp_protocol_version="2025-06-18",
        state_dir=tmp_path,
        audit_log_path=tmp_path / "audit.jsonl",
        dry_run=True,
        live_trading=False,
        max_order_notional_usd=None,
        symbol_allowlist=frozenset(),
        market_hours_only=False,
        allow_fractional_equities=True,
        local_mcp_bearer_token=None,
        allow_docker_loopback_bind=False,
        auth_redirect_uri="http://127.0.0.1:8765/callback",
        auth_callback_bind_host="127.0.0.1",
        auth_callback_port=8765,
        oauth_client_id=None,
        oauth_client_secret=None,
        request_timeout_seconds=30,
    )


@pytest.mark.anyio
async def test_filters_upstream_tools_to_all_22_allowed_tools(tmp_path):
    service = BridgeService(settings(tmp_path))
    service.upstream = FakeUpstream(
        tools=ALL_TOOL_SCHEMAS + [{"name": "place_option_order", "inputSchema": {"type": "object"}}]
    )
    tools = await service.load_allowed_tools(force=True)
    assert [tool["name"] for tool in tools] == list(ALLOWED_TOOLS)
    assert len(tools) == 22


@pytest.mark.anyio
async def test_blocks_non_allowlisted_tool(tmp_path):
    service = BridgeService(settings(tmp_path))
    service.upstream = FakeUpstream()
    response = await service.handle_tools_call(
        "blocked",
        {"name": "place_option_order", "arguments": {}},
        "client",
    )
    result = response["result"]
    assert result["isError"] is True
    assert result["structuredContent"]["reason"] == "tool_not_allowlisted"


@pytest.mark.anyio
async def test_watchlist_mutation_forwards_and_audits(tmp_path):
    service = BridgeService(settings(tmp_path))
    upstream = FakeUpstream()
    service.upstream = upstream
    response = await service.handle_tools_call(
        "watchlist",
        {
            "name": "create_watchlist",
            "arguments": {"display_name": "Test List"},
        },
        "client",
    )
    assert response["result"]["structuredContent"] == {"ok": True}
    assert upstream.calls[-1]["method"] == "tools/call"
    assert upstream.calls[-1]["params"]["name"] == "create_watchlist"
    audit_lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    audit = json.loads(audit_lines[-1])
    assert audit["tool_name"] == "create_watchlist"
    assert audit["decision"] == "forwarded"


@pytest.mark.anyio
async def test_place_equity_order_still_requires_recent_review(tmp_path):
    service = BridgeService(settings(tmp_path))
    service.upstream = FakeUpstream()
    response = await service.handle_tools_call(
        "place",
        {
            "name": "place_equity_order",
            "arguments": {
                "account_number": "123456789",
                "symbol": "AAPL",
                "side": "buy",
                "type": "market",
                "quantity": "1",
            },
        },
        "client",
    )
    assert response["result"]["isError"] is True
    assert response["result"]["structuredContent"]["requirement"].startswith("Call review_equity_order")


@pytest.mark.anyio
async def test_place_equity_order_dry_run_after_review(tmp_path):
    service = BridgeService(settings(tmp_path))
    service.upstream = FakeUpstream()
    args = {
        "account_number": "123456789",
        "symbol": "AAPL",
        "side": "buy",
        "type": "limit",
        "quantity": "1",
        "limit_price": "100",
    }
    await service.review_cache.record("client", args)
    response = await service.handle_tools_call(
        "place",
        {"name": "place_equity_order", "arguments": args},
        "client",
    )
    assert response["result"]["structuredContent"]["dry_run"] is True
    assert response["result"]["structuredContent"]["forwarded"] is False
