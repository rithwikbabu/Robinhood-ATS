# Architecture

The package has three small layers.

## Local MCP bridge

`robinhood_mcp_bridge.server` exposes `POST /mcp` and implements the minimal JSON-RPC methods needed by MCP clients:

- `initialize`
- `ping`
- `tools/list`
- `tools/call`

It filters upstream tools to `SUPPORTED_TOOLS` and forwards calls without changing upstream schemas.

## Upstream Robinhood MCP access

`robinhood_mcp_bridge.auth` handles OAuth discovery, login, refresh, and token storage.

`robinhood_mcp_bridge.upstream` sends JSON-RPC calls to Robinhood's official Agentic Trading MCP.

The package does not use private Robinhood web or mobile APIs.

## Thin Python SDK

`robinhood_mcp_bridge.sdk` is a convenience wrapper around local MCP `tools/call`.

The SDK should stay thin:

- no trading strategies
- no portfolio analysis
- no account-state cache
- no alternate schemas

Safety logic belongs in the bridge, not the SDK.
