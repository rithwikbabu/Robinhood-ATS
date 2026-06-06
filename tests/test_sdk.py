from __future__ import annotations

import httpx
import pytest

from robinhood_mcp_bridge.sdk import RobinhoodMCPClient
from robinhood_mcp_bridge.tools import ALLOWED_TOOLS


def test_sdk_default_url_matches_local_bridge():
    client = RobinhoodMCPClient()
    assert client.url == "http://127.0.0.1:8080/mcp"


class FakeResponse:
    def __init__(self):
        self.payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "content": [{"type": "text", "text": "{}"}],
                "structuredContent": {"ok": True},
            },
        }

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_sdk_methods_emit_expected_tool_calls(monkeypatch):
    calls = []

    def fake_post(url, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    client = RobinhoodMCPClient("http://bridge/mcp", bearer_token="local", timeout=5)

    samples = {
        "add_option_to_watchlist": lambda: client.add_option_to_watchlist(option_ids=["opt"]),
        "add_to_watchlist": lambda: client.add_to_watchlist(list_id="list", symbols=["AAPL"]),
        "cancel_equity_order": lambda: client.cancel_equity_order(account_number="acct", order_id="order"),
        "create_watchlist": lambda: client.create_watchlist(display_name="List"),
        "follow_list": lambda: client.follow_list(list_id="list"),
        "get_accounts": client.get_accounts,
        "get_equity_orders": lambda: client.get_equity_orders(account_number="acct"),
        "get_equity_positions": lambda: client.get_equity_positions(account_number="acct"),
        "get_equity_quotes": lambda: client.get_equity_quotes(symbols=["AAPL"]),
        "get_equity_tradability": lambda: client.get_equity_tradability(account_number="acct", symbols=["AAPL"]),
        "get_options_watchlist": client.get_options_watchlist,
        "get_popular_lists": client.get_popular_lists,
        "get_portfolio": lambda: client.get_portfolio(account_number="acct"),
        "get_watchlist_items": lambda: client.get_watchlist_items(list_id="list"),
        "get_watchlists": client.get_watchlists,
        "place_equity_order": lambda: client.place_equity_order(account_number="acct", symbol="AAPL", side="buy", type="market"),
        "remove_from_watchlist": lambda: client.remove_from_watchlist(list_id="list", symbols=["AAPL"]),
        "remove_option_from_watchlist": lambda: client.remove_option_from_watchlist(option_ids=["opt"]),
        "review_equity_order": lambda: client.review_equity_order(account_number="acct", symbol="AAPL", side="buy", type="market"),
        "search": lambda: client.search(query="Apple"),
        "unfollow_list": lambda: client.unfollow_list(list_id="list"),
        "update_watchlist": lambda: client.update_watchlist(list_id="list", display_name="New"),
    }

    for expected_name in ALLOWED_TOOLS:
        result = samples[expected_name]()
        assert result["structuredContent"] == {"ok": True}
        payload = calls[-1]["json"]
        assert payload["method"] == "tools/call"
        assert payload["params"]["name"] == expected_name

    assert len(calls) == len(ALLOWED_TOOLS)
    assert calls[0]["url"] == "http://bridge/mcp"
    assert calls[0]["headers"]["Authorization"] == "Bearer local"
