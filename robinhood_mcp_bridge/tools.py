from __future__ import annotations


SUPPORTED_TOOLS: tuple[str, ...] = (
    "add_option_to_watchlist",
    "add_to_watchlist",
    "cancel_equity_order",
    "create_watchlist",
    "follow_list",
    "get_accounts",
    "get_equity_orders",
    "get_equity_positions",
    "get_equity_quotes",
    "get_equity_tradability",
    "get_options_watchlist",
    "get_popular_lists",
    "get_portfolio",
    "get_watchlist_items",
    "get_watchlists",
    "place_equity_order",
    "remove_from_watchlist",
    "remove_option_from_watchlist",
    "review_equity_order",
    "search",
    "unfollow_list",
    "update_watchlist",
)


ALLOWED_TOOLS = SUPPORTED_TOOLS
