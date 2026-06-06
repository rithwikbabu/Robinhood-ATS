from __future__ import annotations

import os

from robinhood_mcp_bridge import RobinhoodMCPClient


client = RobinhoodMCPClient(
    os.getenv("ROBINHOOD_MCP_BRIDGE_URL", "http://127.0.0.1:8080/mcp"),
    bearer_token=os.getenv("LOCAL_MCP_BEARER_TOKEN") or None,
)

print(client.search(query="Apple", asset_type="instrument", limit=3)["structuredContent"])
