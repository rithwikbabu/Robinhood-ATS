from __future__ import annotations

import os

from robinhood_mcp_bridge import RobinhoodMCPClient


def main() -> None:
    client = RobinhoodMCPClient(
        os.getenv("ROBINHOOD_MCP_BRIDGE_URL", "http://127.0.0.1:8080/mcp"),
        bearer_token=os.getenv("LOCAL_MCP_BEARER_TOKEN") or None,
    )
    accounts = client.get_accounts()
    quotes = client.get_equity_quotes(symbols=["AAPL"])

    print("accounts:")
    print(accounts["structuredContent"]["data"])
    print("\nAAPL quote:")
    print(quotes["structuredContent"]["data"])


if __name__ == "__main__":
    main()
