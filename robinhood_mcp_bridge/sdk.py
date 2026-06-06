from __future__ import annotations

import itertools
from typing import Any

import httpx


class RobinhoodMCPError(RuntimeError):
    def __init__(self, code: int, message: str, data: Any | None = None):
        super().__init__(f"MCP error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class RobinhoodMCPClient:
    def __init__(
        self,
        url: str = "http://127.0.0.1:8080/mcp",
        *,
        bearer_token: str | None = None,
        timeout: float = 30.0,
    ):
        self.url = url
        self.bearer_token = bearer_token
        self.timeout = timeout
        self._ids = itertools.count(1)

    def call_tool(self, name: str, **arguments: Any) -> dict[str, Any]:
        response = self.request(
            {
                "jsonrpc": "2.0",
                "id": f"tool-{next(self._ids)}",
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        return response["result"]

    def list_tools(self) -> list[dict[str, Any]]:
        response = self.request(
            {
                "jsonrpc": "2.0",
                "id": f"tools-{next(self._ids)}",
                "method": "tools/list",
                "params": {},
            }
        )
        return response["result"]["tools"]

    def initialize(self) -> dict[str, Any]:
        response = self.request(
            {
                "jsonrpc": "2.0",
                "id": f"init-{next(self._ids)}",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "robinhood-mcp-bridge-sdk",
                        "version": "0.1.0",
                    },
                },
            }
        )
        return response["result"]

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        response = httpx.post(self.url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            error = data["error"]
            raise RobinhoodMCPError(
                int(error.get("code", -32000)),
                str(error.get("message", "Unknown MCP error")),
                error.get("data"),
            )
        return data

    def add_option_to_watchlist(
        self,
        option_ids: list[str],
        position_type: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "add_option_to_watchlist",
            **_drop_none(option_ids=option_ids, position_type=position_type),
        )

    def add_to_watchlist(
        self,
        list_id: str,
        symbols: list[str] | None = None,
        currency_pair_ids: list[str] | None = None,
        index_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "add_to_watchlist",
            **_drop_none(
                list_id=list_id,
                symbols=symbols,
                currency_pair_ids=currency_pair_ids,
                index_ids=index_ids,
            ),
        )

    def cancel_equity_order(self, account_number: str, order_id: str) -> dict[str, Any]:
        return self.call_tool(
            "cancel_equity_order",
            account_number=account_number,
            order_id=order_id,
        )

    def create_watchlist(
        self,
        display_name: str,
        display_description: str | None = None,
        icon_emoji: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "create_watchlist",
            **_drop_none(
                display_name=display_name,
                display_description=display_description,
                icon_emoji=icon_emoji,
            ),
        )

    def follow_list(self, list_id: str) -> dict[str, Any]:
        return self.call_tool("follow_list", list_id=list_id)

    def get_accounts(self) -> dict[str, Any]:
        return self.call_tool("get_accounts")

    def get_equity_orders(
        self,
        account_number: str,
        created_at_gte: str | None = None,
        cursor: str | None = None,
        order_id: str | None = None,
        placed_agent: str | None = None,
        state: str | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "get_equity_orders",
            **_drop_none(
                account_number=account_number,
                created_at_gte=created_at_gte,
                cursor=cursor,
                order_id=order_id,
                placed_agent=placed_agent,
                state=state,
                symbol=symbol,
            ),
        )

    def get_equity_positions(
        self,
        account_number: str,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "get_equity_positions",
            **_drop_none(account_number=account_number, cursor=cursor),
        )

    def get_equity_quotes(self, symbols: list[str] | None) -> dict[str, Any]:
        return self.call_tool("get_equity_quotes", symbols=symbols)

    def get_equity_tradability(
        self,
        account_number: str,
        symbols: list[str] | None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "get_equity_tradability",
            account_number=account_number,
            symbols=symbols,
        )

    def get_options_watchlist(self) -> dict[str, Any]:
        return self.call_tool("get_options_watchlist")

    def get_popular_lists(self) -> dict[str, Any]:
        return self.call_tool("get_popular_lists")

    def get_portfolio(self, account_number: str) -> dict[str, Any]:
        return self.call_tool("get_portfolio", account_number=account_number)

    def get_watchlist_items(self, list_id: str) -> dict[str, Any]:
        return self.call_tool("get_watchlist_items", list_id=list_id)

    def get_watchlists(self) -> dict[str, Any]:
        return self.call_tool("get_watchlists")

    def place_equity_order(
        self,
        account_number: str,
        symbol: str,
        side: str,
        type: str,
        dollar_amount: str | None = None,
        limit_price: str | None = None,
        market_hours: str | None = None,
        quantity: str | None = None,
        ref_id: str | None = None,
        stop_price: str | None = None,
        time_in_force: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "place_equity_order",
            **_drop_none(
                account_number=account_number,
                symbol=symbol,
                side=side,
                type=type,
                dollar_amount=dollar_amount,
                limit_price=limit_price,
                market_hours=market_hours,
                quantity=quantity,
                ref_id=ref_id,
                stop_price=stop_price,
                time_in_force=time_in_force,
            ),
        )

    def remove_from_watchlist(
        self,
        list_id: str,
        symbols: list[str] | None = None,
        currency_pair_ids: list[str] | None = None,
        index_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "remove_from_watchlist",
            **_drop_none(
                list_id=list_id,
                symbols=symbols,
                currency_pair_ids=currency_pair_ids,
                index_ids=index_ids,
            ),
        )

    def remove_option_from_watchlist(
        self,
        option_ids: list[str],
        position_type: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "remove_option_from_watchlist",
            **_drop_none(option_ids=option_ids, position_type=position_type),
        )

    def review_equity_order(
        self,
        account_number: str,
        symbol: str,
        side: str,
        type: str,
        dollar_amount: str | None = None,
        limit_price: str | None = None,
        market_hours: str | None = None,
        quantity: str | None = None,
        stop_price: str | None = None,
        time_in_force: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "review_equity_order",
            **_drop_none(
                account_number=account_number,
                symbol=symbol,
                side=side,
                type=type,
                dollar_amount=dollar_amount,
                limit_price=limit_price,
                market_hours=market_hours,
                quantity=quantity,
                stop_price=stop_price,
                time_in_force=time_in_force,
            ),
        )

    def search(
        self,
        query: str,
        asset_type: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "search",
            **_drop_none(query=query, asset_type=asset_type, limit=limit),
        )

    def unfollow_list(self, list_id: str) -> dict[str, Any]:
        return self.call_tool("unfollow_list", list_id=list_id)

    def update_watchlist(
        self,
        list_id: str,
        display_name: str | None = None,
        display_description: str | None = None,
        icon_emoji: str | None = None,
    ) -> dict[str, Any]:
        return self.call_tool(
            "update_watchlist",
            **_drop_none(
                list_id=list_id,
                display_name=display_name,
                display_description=display_description,
                icon_emoji=icon_emoji,
            ),
        )


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}
