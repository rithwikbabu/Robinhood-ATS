# Robinhood MCP Bridge

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/rithwikbabu/Robinhood-ATS/actions/workflows/ci.yml/badge.svg)](https://github.com/rithwikbabu/Robinhood-ATS/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-black)](https://rithwikbabu.github.io/Robinhood-ATS/)

Lean local MCP bridge and Python client for Robinhood Agentic Trading.

Documentation: <https://rithwikbabu.github.io/Robinhood-ATS/>

It gives you:

- A local Streamable HTTP MCP endpoint at `http://127.0.0.1:8080/mcp`.
- A tiny Python SDK for calling that local bridge.
- One-command Docker-first setup with OAuth token storage in `.rh-mcp-state/`.
- Docker Compose publishes the bridge on host loopback only by default.
- Safe defaults: real equity order placement is disabled unless explicitly enabled.

Names:

- Package/distribution: `robinhood-mcp-bridge`
- Python import: `robinhood_mcp_bridge`
- CLI: `rh-mcp` or `robinhood-mcp-bridge`

It forwards the full supported v1 tool allowlist to Robinhood's official Trading MCP:

```text
https://agent.robinhood.com/mcp/trading
```

It does not use private Robinhood web or mobile APIs.

This is an independent open-source project and is not affiliated with, endorsed by, or maintained by Robinhood.

## Contents

- [Fastest setup](#fastest-setup)
- [Install](#install)
- [Quick start](#quick-start)
- [Command reference](docs/commands.md)
- [Supported tools](#supported-tools)
- [Python SDK](#python-sdk)
- [Safety defaults](#safety-defaults)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Fastest setup

For the shortest path, see [docs/quickstart.md](docs/quickstart.md).
For a compact command reference, see [docs/commands.md](docs/commands.md).

```bash
make bootstrap
```

## Install

Minimum requirements:

- Docker with Docker Compose for the local bridge.
- Python 3.11+ only if you want the SDK, local CLI, or contributor tooling.

Use Docker for the bridge:

```bash
git clone https://github.com/rithwikbabu/Robinhood-ATS.git
cd Robinhood-ATS
make
make bootstrap
```

Plain `make` prints the command help.

No `make` installed: use the raw Docker Compose sequence in [Quick start](#quick-start).

For a released package, use pip for the optional Python SDK and CLI:

```bash
pip install robinhood-mcp-bridge
```

For local development from this checkout:

```bash
pip install -e .
```

For contributor tooling:

```bash
pip install -e ".[dev]"
```

This also installs a short local CLI. For Python-only local runs:

```bash
rh-mcp auth
rh-mcp serve
```

Then in another terminal:

```bash
rh-mcp ready
```

Use `python -m robinhood_mcp_bridge ...` if the `rh-mcp` console script is not on `PATH`.
See [docs/commands.md](docs/commands.md) for the full Python CLI command list.

The Python CLI reads process environment variables directly. The `.env` file is for Docker Compose.

## Quick start

First-time setup opens a browser-based Robinhood OAuth login, starts the bridge, and checks it:

```bash
make bootstrap
```

No `make` installed:

```bash
cp .env.example .env
mkdir -p .rh-mcp-state
docker compose build
docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth
docker compose up -d
docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready
```

The common `make` commands create `.env` and `.rh-mcp-state/` automatically if needed.
`make auth` also asks Docker Compose to build the image before login.
`make bootstrap` starts the bridge, prints the endpoint, and runs the readiness check.

Check the running bridge again:

```bash
make ps
make ready
make url
```

For individual checks, use `make doctor`, `make status`, `make tools`, and `make smoke`.

Stop it:

```bash
make stop
```

Useful service commands:

```bash
make logs
make stop
```

Smoke-test the running bridge:

```bash
make smoke
```

The smoke test checks MCP handshake and tool exposure only; it does not read accounts or submit order-related calls.

No `make` installed:

```bash
docker compose exec -T robinhood-mcp robinhood-mcp-bridge smoke
```

Point any Streamable HTTP MCP client at:

```text
http://127.0.0.1:8080/mcp
```

Example MCP client config:

```json
{
  "mcpServers": {
    "robinhood": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

The same JSON is available in `examples/mcp-client-config.json`.

If you set `LOCAL_MCP_BEARER_TOKEN`, use `examples/mcp-client-config-with-token.json` as the shape for clients that support custom headers.

See `docs/mcp-clients.md` for MCP client setup notes.

Or call it from Python:

```python
from robinhood_mcp_bridge import RobinhoodMCPClient
from robinhood_mcp_bridge import SUPPORTED_TOOLS

client = RobinhoodMCPClient()

accounts = client.get_accounts()
quotes = client.get_equity_quotes(symbols=["AAPL"])
watchlists = client.get_watchlists()
print(SUPPORTED_TOOLS)
```

Run the read-only example:

```bash
python examples/quickstart.py
python examples/read_only.py
```

The bundled examples are read-only. They do not review, place, or cancel orders.
See [examples/README.md](examples/README.md) for example-specific setup notes.

For local Python-only development, use the `rh-mcp` commands in [docs/commands.md](docs/commands.md).

## Troubleshooting

For short answers to first-run questions, see [docs/faq.md](docs/faq.md).

- `auth: executable file not found`: rebuild the image with `docker compose build`; the image uses `robinhood-mcp-bridge` as its entrypoint.
- `Could not discover OAuth authorization server metadata`: rebuild; current code supports Robinhood's path-based OAuth issuer metadata.
- `No upstream OAuth token`: run `make bootstrap` or `docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth`.
- Bad or stale local auth state: run `make reset-state`, then `make bootstrap`. This removes saved OAuth tokens, cached schemas, and local audit logs under `.rh-mcp-state/`.
- Permission error writing tokens: run `make reset-state`, then `make bootstrap`. This removes saved OAuth tokens, cached schemas, and local audit logs under `.rh-mcp-state/`.
- `Address already in use` during `make start`: free port `8080`, stop the old bridge with `make stop`, or set `MCP_HOST_PORT=8081` in `.env`, then retry.
- For a one-off bridge port override during first setup, run `MCP_HOST_PORT=8081 make bootstrap`.
- For later starts, run `MCP_HOST_PORT=8081 make start`.
- `Address already in use` during `make auth`: free port `8765`; that port is used only for the OAuth callback during login.
- If port `8765` is unavailable during first setup, set `AUTH_HOST_PORT=8766` in `.env`, then run `make bootstrap`.
- For a one-off auth callback port override, run `AUTH_HOST_PORT=8766 make auth`.
- `make smoke` fails before auth: authenticate first, because `tools/list` needs upstream Robinhood MCP access unless cached schemas already exist.
- If the bridge is not running, check `make ps`, then start it with `make start`.

## Project boundaries

This package is intentionally narrow:

- It bridges to Robinhood's official Agentic Trading MCP.
- It provides a thin Python client for the local bridge.
- It does not implement strategies, portfolio advice, private Robinhood APIs, or background trading automation.
- It keeps real equity order placement opt-in and guarded.

See `docs/known-limits.md` for explicit non-goals.

## Supported tools

The local `tools/list` response is filtered to the 22 currently supported upstream tools:

You can print this list locally with `make tools` or `rh-mcp tools`.

```text
add_option_to_watchlist
add_to_watchlist
cancel_equity_order
create_watchlist
follow_list
get_accounts
get_equity_orders
get_equity_positions
get_equity_quotes
get_equity_tradability
get_options_watchlist
get_popular_lists
get_portfolio
get_watchlist_items
get_watchlists
place_equity_order
remove_from_watchlist
remove_option_from_watchlist
review_equity_order
search
unfollow_list
update_watchlist
```

Any upstream tool not in this list is intentionally hidden.

If you run without publishing `127.0.0.1:8765:8765`, the login command can still complete by asking you to paste the final callback URL after Robinhood redirects.

## Python SDK

The raw MCP endpoint remains the primary interface. The package also includes a convenience SDK that calls the local bridge:

The SDK does not authenticate to Robinhood directly; start the local bridge first.

```python
from robinhood_mcp_bridge import RobinhoodMCPClient

client = RobinhoodMCPClient()

accounts = client.get_accounts()
quotes = client.get_equity_quotes(symbols=["AAPL"])
watchlists = client.get_watchlists()
created = client.create_watchlist(display_name="My List")
```

If you changed `MCP_HOST_PORT`, pass the URL printed by `make url`.
If you set `LOCAL_MCP_BEARER_TOKEN`, pass it as `bearer_token=...`.

The SDK exposes one method per supported tool and returns the MCP tool result object unchanged, preserving `content`, `structuredContent`, and `isError`.

See `docs/sdk-reference.md` for the method list.

## Safety defaults

`DRY_RUN=true` by default. In dry-run mode, read tools, watchlist/list mutations, and `review_equity_order` forward upstream, but `place_equity_order` is not forwarded to Robinhood.

To place live orders, all of these must be true:

```bash
DRY_RUN=false
LIVE_TRADING=true
```

Every `place_equity_order` must match a successful `review_equity_order` from the same local client within the last 60 seconds.

Watchlist/list mutations are forwarded directly and recorded in the audit log. Equity order placement is the only mutation with the extra trading guardrails above.

To opt into live equity placement, edit `.env`:

```text
DRY_RUN=false
LIVE_TRADING=true
```

Then restart the bridge and call `review_equity_order` before `place_equity_order` with matching arguments.

## Configuration

Key environment variables:

```text
ROBINHOOD_MCP_URL=https://agent.robinhood.com/mcp/trading
DRY_RUN=true
LIVE_TRADING=false
MAX_ORDER_NOTIONAL_USD=
SYMBOL_ALLOWLIST=
MARKET_HOURS_ONLY=true
ALLOW_FRACTIONAL_EQUITIES=true
LOCAL_MCP_BEARER_TOKEN=
```

Copy `.env.example` to `.env` for local Docker usage.

`SYMBOL_ALLOWLIST` is comma-separated, for example:

```bash
SYMBOL_ALLOWLIST=AAPL,MSFT,VOO
```

`MAX_ORDER_NOTIONAL_USD` is optional. When set, live `place_equity_order` calls are blocked if the bridge cannot estimate notional from the tool arguments.

See `docs/configuration.md` for the full configuration reference.

## Local auth on the bridge

For local development, the Docker compose file publishes the container only on host loopback:

```text
127.0.0.1:8080
```

If you bind the bridge itself to `0.0.0.0` outside the compose file, set `LOCAL_MCP_BEARER_TOKEN` or the service refuses to start.
Built-in checks such as `make ready` and `make smoke` use this token automatically.

Do not expose this service on a public network without transport security and a strong local bearer token.

## Audit log

Tool calls are written as JSONL to:

```text
.rh-mcp-state/audit.jsonl
```

The audit log redacts credentials and masks full account numbers.

## Financial risk

Robinhood Agentic Trading can place real trades through a dedicated Agentic account. Real order placement is opt-in here, but you are responsible for all trades and losses.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make check
```

Keep this package small. The bridge should stay focused on official Robinhood MCP forwarding, local safety controls, and a minimal Python client.

CI runs Python tests on 3.11 and 3.12 and verifies the Docker image builds.

See `docs/testing.md` for local checks and smoke-test expectations.

See `docs/faq.md` for common setup questions.

See `RELEASE.md` before publishing a package or image.

Build local package artifacts with `make build-package`.
Clean local build and test caches with `make clean`.

See `CHANGELOG.md` for release notes.

## License

MIT. See `LICENSE`.
