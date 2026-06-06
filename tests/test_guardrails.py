from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from robinhood_mcp_bridge.config import Settings
from robinhood_mcp_bridge.guardrails import GuardrailEngine, ReviewCache, estimate_notional_usd


def base_settings(tmp_path):
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


def test_estimates_notional_from_quantity_and_price():
    assert estimate_notional_usd({"symbol": "AAPL", "quantity": "2", "limit_price": "10.50"}) == Decimal("21.00")


@pytest.mark.anyio
async def test_blocks_place_without_recent_review(tmp_path):
    cache = ReviewCache()
    engine = GuardrailEngine(base_settings(tmp_path), cache)
    decision = await engine.validate_place(client_id="c1", arguments={"symbol": "AAPL"})
    assert not decision.allowed
    assert decision.reason == "missing_recent_review"


@pytest.mark.anyio
async def test_blocks_symbol_not_allowlisted_after_review(tmp_path):
    cache = ReviewCache()
    args = {"symbol": "TSLA", "quantity": "1", "limit_price": "100"}
    await cache.record("c1", args)
    settings = replace(base_settings(tmp_path), symbol_allowlist=frozenset({"AAPL"}))
    engine = GuardrailEngine(settings, cache)
    decision = await engine.validate_place(client_id="c1", arguments=args)
    assert not decision.allowed
    assert decision.reason == "symbol_not_allowlisted"


@pytest.mark.anyio
async def test_blocks_max_notional(tmp_path):
    cache = ReviewCache()
    args = {"symbol": "AAPL", "quantity": "2", "limit_price": "100"}
    await cache.record("c1", args)
    settings = replace(base_settings(tmp_path), max_order_notional_usd=Decimal("100"))
    engine = GuardrailEngine(settings, cache)
    decision = await engine.validate_place(client_id="c1", arguments=args)
    assert not decision.allowed
    assert decision.reason == "max_order_notional_exceeded"
