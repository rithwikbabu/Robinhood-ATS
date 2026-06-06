# FAQ

## Is this an official Robinhood package?

No. This project is independent. It connects to Robinhood's official Agentic Trading MCP endpoint and adds a small local bridge, CLI, Docker setup, SDK, and safety defaults.

## Does the Python SDK authenticate directly with Robinhood?

No. The SDK talks to a running local bridge. Run `make bootstrap`, then point the SDK at `http://127.0.0.1:8080/mcp`.

## Do the examples place trades?

No. The bundled examples are read-only unless clearly documented otherwise.

## Is live trading enabled by default?

No. The default environment is conservative:

- `DRY_RUN=true`
- `LIVE_TRADING=false`
- `SYMBOL_ALLOWLIST` empty
- `MAX_ORDER_NOTIONAL_USD` unset
- `MARKET_HOURS_ONLY=true`

Order placement also requires a recent successful `review_equity_order` from the same local client. Real placement remains blocked until you deliberately change the live-trading settings.

## Where are auth tokens stored?

Docker usage stores bridge state under `.rh-mcp-state/`. Treat that directory as sensitive. It is ignored by git.

## Can I expose the bridge on the public internet?

Not by default. The compose file binds to `127.0.0.1`, and the bridge is designed for local use. If you deploy it behind a network boundary, add TLS, a strong bearer token, and your own operational controls.

## Do I need Python installed?

For Docker-only use, you need Docker and Docker Compose. Python is only needed for local development, the SDK, or running the package directly without Docker.

## What should I run first?

For the shortest path:

```bash
make bootstrap
```

`make smoke` is intentionally account-data-free and non-trading.

See [quickstart.md](quickstart.md) for the full first-run sequence.
