# Configuration

Copy `.env.example` to `.env` for Docker usage.

```bash
cp .env.example .env
```

## Core settings

| Variable | Default | Purpose |
|---|---|---|
| `ROBINHOOD_MCP_URL` | `https://agent.robinhood.com/mcp/trading` | Upstream official Robinhood Agentic Trading MCP URL. |
| `MCP_HOST_PORT` | `8080` | Host port published by Docker Compose for the local MCP bridge. |
| `LOCAL_MCP_BEARER_TOKEN` | unset | Optional local bearer token for MCP clients. |

## Python CLI bind settings

These apply when running `rh-mcp serve` or `python -m robinhood_mcp_bridge serve` outside Docker.

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Local bind host for the Python CLI server. |
| `PORT` | `8080` | Local bind port for the Python CLI server. |

For Docker Compose, prefer `MCP_HOST_PORT` instead of `PORT`; the container still listens on port `8080` internally.

## State paths

Docker stores OAuth tokens, cached schemas, and audit logs in `.rh-mcp-state/` on the host, mounted as `/state` in the container.

Direct Python usage defaults to:

| Variable | Default | Purpose |
|---|---|---|
| `STATE_DIR` | `.rh-mcp-state` | OAuth token and schema cache storage. |
| `AUDIT_LOG_PATH` | `.rh-mcp-state/audit.jsonl` | JSONL audit log path. |

## Trading safety

| Variable | Default | Purpose |
|---|---|---|
| `DRY_RUN` | `true` | Prevents forwarding `place_equity_order`. |
| `LIVE_TRADING` | `false` | Must be `true` before real equity orders can forward. |
| `MAX_ORDER_NOTIONAL_USD` | unset | Optional max estimated order notional. |
| `SYMBOL_ALLOWLIST` | unset | Optional comma-separated symbol allowlist. |
| `MARKET_HOURS_ONLY` | `true` | Blocks equity placement outside regular US market hours. |
| `ALLOW_FRACTIONAL_EQUITIES` | `true` | Allows fractional equity quantities. |

`place_equity_order` also requires a matching successful `review_equity_order` from the same local client within 60 seconds.

## OAuth callback

| Variable | Default | Purpose |
|---|---|---|
| `AUTH_HOST_PORT` | `8765` | Host port published by `make auth` for the OAuth callback. |
| `AUTH_REDIRECT_URI` | `http://127.0.0.1:8765/callback` | Redirect URI used during browser login. |
| `AUTH_CALLBACK_BIND_HOST` | `0.0.0.0` in Docker | Callback listener bind host. |
| `AUTH_CALLBACK_PORT` | `8765` | Callback listener port. |

Use `docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth` so the callback port is published during login.

If host port `8765` is unavailable and you use `make auth`, set another host port in `.env`:

```bash
AUTH_HOST_PORT=8766
make auth
```

`make auth` derives `AUTH_REDIRECT_URI` from `AUTH_HOST_PORT` unless you set `AUTH_REDIRECT_URI` explicitly.
Leave `AUTH_REDIRECT_URI` commented in `.env` unless you need a custom redirect URI.

For direct Python usage, set both variables in your shell if port `8765` is unavailable:

```bash
AUTH_CALLBACK_PORT=8766 AUTH_REDIRECT_URI=http://127.0.0.1:8766/callback rh-mcp auth
```
