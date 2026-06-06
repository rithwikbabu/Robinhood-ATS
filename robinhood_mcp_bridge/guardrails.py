from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from .config import Settings
from .mcp import canonical_json
from .tools import ALLOWED_TOOLS


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    reason: str
    details: dict[str, Any]


class ReviewCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = timedelta(seconds=ttl_seconds)
        self._items: dict[tuple[str, str], datetime] = {}
        self._lock = asyncio.Lock()

    async def record(self, client_id: str, arguments: dict[str, Any]) -> None:
        async with self._lock:
            self._items[(client_id, canonical_json(arguments))] = datetime.utcnow() + self.ttl

    async def has_recent(self, client_id: str, arguments: dict[str, Any]) -> bool:
        now = datetime.utcnow()
        fingerprint = canonical_json(arguments)
        async with self._lock:
            expired = [key for key, expires_at in self._items.items() if expires_at <= now]
            for key in expired:
                self._items.pop(key, None)
            return self._items.get((client_id, fingerprint), datetime.min) > now


def decimal_from_value(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def walk_dicts(value: Any) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            items.append((str(key), item))
            items.extend(walk_dicts(item))
    elif isinstance(value, list):
        for item in value:
            items.extend(walk_dicts(item))
    return items


def extract_symbol(arguments: dict[str, Any]) -> str | None:
    symbol_keys = {"symbol", "ticker", "equity_symbol", "instrument_symbol"}
    for key, value in walk_dicts(arguments):
        if key.lower() in symbol_keys and isinstance(value, str) and value.strip():
            return value.strip().upper()
    return None


def estimate_notional_usd(arguments: dict[str, Any]) -> Decimal | None:
    notional_keys = {
        "notional",
        "notional_amount",
        "dollar_amount",
        "cash_amount",
        "amount_usd",
        "usd_amount",
        "market_value",
    }
    quantity_keys = {
        "quantity",
        "qty",
        "shares",
        "share_quantity",
        "fractional_quantity",
    }
    price_keys = {
        "price",
        "limit_price",
        "stop_price",
        "estimated_price",
    }

    quantities: list[Decimal] = []
    prices: list[Decimal] = []

    for key, value in walk_dicts(arguments):
        key_lower = key.lower()
        number = decimal_from_value(value)
        if number is None:
            continue
        if key_lower in notional_keys:
            return abs(number)
        if key_lower in quantity_keys:
            quantities.append(abs(number))
        if key_lower in price_keys:
            prices.append(abs(number))

    if quantities and prices:
        return quantities[0] * prices[0]
    return None


def has_fractional_quantity(arguments: dict[str, Any]) -> bool:
    quantity_keys = {
        "quantity",
        "qty",
        "shares",
        "share_quantity",
        "fractional_quantity",
    }
    for key, value in walk_dicts(arguments):
        if key.lower() not in quantity_keys:
            continue
        number = decimal_from_value(value)
        if number is not None and number != number.to_integral_value():
            return True
    return False


def is_regular_market_hours(now: datetime | None = None) -> bool:
    eastern = ZoneInfo("America/New_York")
    current = now.astimezone(eastern) if now else datetime.now(eastern)
    if current.weekday() >= 5:
        return False
    return time(9, 30) <= current.time() <= time(16, 0)


class GuardrailEngine:
    def __init__(self, settings: Settings, review_cache: ReviewCache):
        self.settings = settings
        self.review_cache = review_cache

    async def validate_place(
        self,
        *,
        client_id: str,
        arguments: dict[str, Any],
    ) -> GuardrailDecision:
        if not await self.review_cache.has_recent(client_id, arguments):
            return GuardrailDecision(
                False,
                "missing_recent_review",
                {"requirement": "Call review_equity_order with identical arguments first."},
            )

        symbol = extract_symbol(arguments)
        if self.settings.symbol_allowlist and symbol not in self.settings.symbol_allowlist:
            return GuardrailDecision(
                False,
                "symbol_not_allowlisted",
                {"symbol": symbol, "allowlist": sorted(self.settings.symbol_allowlist)},
            )

        if self.settings.market_hours_only and not is_regular_market_hours():
            return GuardrailDecision(
                False,
                "outside_regular_market_hours",
                {"timezone": "America/New_York", "window": "09:30-16:00 weekdays"},
            )

        if not self.settings.allow_fractional_equities and has_fractional_quantity(arguments):
            return GuardrailDecision(
                False,
                "fractional_equities_disabled",
                {"allow_fractional_equities": False},
            )

        notional = estimate_notional_usd(arguments)
        max_notional = self.settings.max_order_notional_usd
        if max_notional is not None:
            if notional is None:
                return GuardrailDecision(
                    False,
                    "notional_could_not_be_estimated",
                    {"max_order_notional_usd": str(max_notional)},
                )
            if notional > max_notional:
                return GuardrailDecision(
                    False,
                    "max_order_notional_exceeded",
                    {
                        "estimated_notional_usd": str(notional),
                        "max_order_notional_usd": str(max_notional),
                    },
                )

        return GuardrailDecision(
            True,
            "allowed",
            {
                "symbol": symbol,
                "estimated_notional_usd": str(notional) if notional is not None else None,
            },
        )
