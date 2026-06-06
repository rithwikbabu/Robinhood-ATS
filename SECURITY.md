# Security Policy

This package can access brokerage account data and can place trades if live trading is explicitly enabled.

This is an independent open-source project and is not affiliated with Robinhood.

## Reporting issues

Please open a private security advisory on GitHub if available, or contact the maintainer without posting secrets publicly.

## Credential handling

- OAuth tokens are stored under `.rh-mcp-state/` or the configured `STATE_DIR`.
- Do not commit `.rh-mcp-state/`, `.env`, audit logs, account numbers, or screenshots containing balances.
- Do not commit local auth or audit files such as `tokens.json`, `oauth_client.json`, `oauth_discovery.json`, or `audit.jsonl`.
- Bind the bridge to `127.0.0.1` unless you set `LOCAL_MCP_BEARER_TOKEN`.
- Do not expose the bridge on a public network without TLS and a strong local bearer token.

## Trading safety

Real equity order placement requires:

```text
DRY_RUN=false
LIVE_TRADING=true
```

The bridge also requires a matching recent `review_equity_order` before `place_equity_order`.
