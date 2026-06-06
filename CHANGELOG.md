# Changelog

## 0.1.0

- Initial local MCP bridge for Robinhood Agentic Trading.
- Docker-first setup with `make bootstrap` to build, authenticate, start the bridge, and check readiness, plus `make ready`, `make start`, `make stop`, and OAuth token storage in `.rh-mcp-state/`.
- Configurable Docker host port through `MCP_HOST_PORT` for users who already have something on port `8080`.
- OAuth callback port `8765` is published only during `make auth`; set `AUTH_HOST_PORT` if that host port is unavailable.
- Full 22-tool supported Robinhood MCP surface exposed through the local bridge.
- Thin Python SDK with one convenience method per supported tool.
- Guardrails for real equity order placement: review requirement, dry-run default, live-trading opt-in, symbol allowlist, notional cap, market-hours check, and fractional-equity setting.
- Local CLI helpers: `init`, `auth`, `doctor`, `status`, `tools`, `url`, `smoke`, and `ready`.
- Open-source docs for quickstart, setup, security, configuration, architecture, SDK usage, MCP clients, and releases.
