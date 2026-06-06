# SDK Reference

The SDK is a thin convenience client over local MCP `tools/call`.

```python
from robinhood_mcp_bridge import RobinhoodMCPClient

client = RobinhoodMCPClient()
```

Each method returns the MCP tool result unchanged.

| MCP tool | SDK method |
|---|---|
| `add_option_to_watchlist` | `client.add_option_to_watchlist(...)` |
| `add_to_watchlist` | `client.add_to_watchlist(...)` |
| `cancel_equity_order` | `client.cancel_equity_order(...)` |
| `create_watchlist` | `client.create_watchlist(...)` |
| `follow_list` | `client.follow_list(...)` |
| `get_accounts` | `client.get_accounts()` |
| `get_equity_orders` | `client.get_equity_orders(...)` |
| `get_equity_positions` | `client.get_equity_positions(...)` |
| `get_equity_quotes` | `client.get_equity_quotes(...)` |
| `get_equity_tradability` | `client.get_equity_tradability(...)` |
| `get_options_watchlist` | `client.get_options_watchlist()` |
| `get_popular_lists` | `client.get_popular_lists()` |
| `get_portfolio` | `client.get_portfolio(...)` |
| `get_watchlist_items` | `client.get_watchlist_items(...)` |
| `get_watchlists` | `client.get_watchlists()` |
| `place_equity_order` | `client.place_equity_order(...)` |
| `remove_from_watchlist` | `client.remove_from_watchlist(...)` |
| `remove_option_from_watchlist` | `client.remove_option_from_watchlist(...)` |
| `review_equity_order` | `client.review_equity_order(...)` |
| `search` | `client.search(...)` |
| `unfollow_list` | `client.unfollow_list(...)` |
| `update_watchlist` | `client.update_watchlist(...)` |

For exact arguments, inspect the live upstream schemas:

```python
for tool in client.list_tools():
    print(tool["name"], tool["inputSchema"])
```
