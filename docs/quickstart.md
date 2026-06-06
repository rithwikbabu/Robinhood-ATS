# Quickstart

This is the shortest Docker-first path.

## 1. Clone and enter the repo

```bash
git clone https://github.com/rithwikbabu/Robinhood-ATS.git
cd Robinhood-ATS
```

## 2. Set up and authenticate

```bash
make bootstrap
```

This creates `.env`, creates `.rh-mcp-state/`, builds the image, opens a browser-based Robinhood MCP OAuth login, starts the local bridge, and runs the readiness check.

The local MCP endpoint is:

```bash
make url
```

Default value: `http://127.0.0.1:8080/mcp`

`make start` also prints the endpoint it started.
`make url` and `rh-mcp url` print the client-facing URL, not the container bind address.

## 3. Check it again

```bash
make ps
make ready
```

`make bootstrap` already runs `make ready`. Run it again any time you want to re-check the bridge.
`make ready` tolerates brief startup lag after `make bootstrap`.
`make smoke` checks the MCP handshake and exposed tool list. It does not read accounts, place orders, or cancel orders.

Stop the bridge with:

```bash
make stop
```

Default ports:

- `8080`: local MCP bridge.
- `8765`: OAuth callback during `make auth` only.

If host port `8080` is unavailable, set `MCP_HOST_PORT=8081` in `.env` and run `make url` again.
For a one-off first setup, use `MCP_HOST_PORT=8081 make bootstrap`.
For later starts, use `MCP_HOST_PORT=8081 make start`.
If host port `8765` is unavailable, set `AUTH_HOST_PORT=8766` in `.env`, then run `make bootstrap` again.
For a one-off login, use `AUTH_HOST_PORT=8766 make auth`.

## No make installed

```bash
cp .env.example .env
mkdir -p .rh-mcp-state
docker compose build
```

Authenticate:

```bash
docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth
```

Start the bridge:

```bash
docker compose up -d
```

Check it:

```bash
docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready
```

## Python CLI path

If you installed the package locally:

```bash
python -m robinhood_mcp_bridge auth
python -m robinhood_mcp_bridge url
python -m robinhood_mcp_bridge serve
```

In another terminal, because `serve` runs in the foreground:

```bash
python -m robinhood_mcp_bridge ready
```
