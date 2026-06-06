# Testing

## Local package checks

Run:

```bash
make check
```

This checks:

- package CLI import and version
- local supported-tool metadata
- unit/static tests
- Docker image build

It does not require Robinhood auth.

## Setup checks

Run after `make bootstrap` or `make start`, with the bridge running:

```bash
make doctor
make ready
```

These inspect local config, local state, and the running bridge tool surface. They do not read account data.
The smoke portion retries briefly to tolerate startup lag after `make bootstrap` or `make start`.
If `LOCAL_MCP_BEARER_TOKEN` is set, `make ready` uses it automatically.

## Bridge smoke test

Run after auth and after the bridge is running:

```bash
make smoke
```

This checks MCP handshake and tool exposure. It does not read accounts, review orders, place orders, or cancel orders.
If `LOCAL_MCP_BEARER_TOKEN` is set, `make smoke` uses it automatically.
