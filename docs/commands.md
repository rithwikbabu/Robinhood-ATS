# Commands

## Docker-first path

| Command | Purpose |
|---|---|
| `make` | Print concise command help and a link to this reference. |
| `make init` | Create `.env` and `.rh-mcp-state/` without authenticating. |
| `make bootstrap` | Create local setup files, build/authenticate, start the bridge, and check readiness. |
| `make auth` | Reauthenticate without starting or checking the bridge. |
| `make start` | Start the local MCP bridge in the background and print its endpoint. |
| `make ps` | Show bridge container status. |
| `make doctor` | Check local setup without contacting Robinhood. |
| `make ready` | Run status, tool-list, and smoke checks against the running bridge. |
| `make smoke` | Check MCP handshake and exposed tools against the running bridge. |
| `make url` | Print the client-facing MCP URL, using `MCP_HOST_PORT` from `.env` when set. |
| `make logs` | Follow bridge logs. |
| `make stop` | Stop the local MCP bridge. |
| `make reset-state` | Remove local OAuth/schema/audit state. |

## Python package path

| Command | Purpose |
|---|---|
| `rh-mcp --help` | Print CLI help. |
| `rh-mcp auth` | Authenticate with Robinhood MCP. |
| `rh-mcp serve` | Run the local bridge without Docker. |
| `rh-mcp url` | Print the client-facing MCP URL. |
| `rh-mcp ready` | Run status, tool-list, and smoke checks. |
| `rh-mcp smoke` | Check MCP handshake and exposed tools. |
| `rh-mcp tools` | Print supported tool names. |
| `rh-mcp doctor` | Check local setup without contacting Robinhood. |

Use `python -m robinhood_mcp_bridge ...` if the console scripts are not on `PATH`.
`rh-mcp serve` runs in the foreground; run `rh-mcp ready` or `rh-mcp smoke` from another terminal.

## No make installed

| Command | Purpose |
|---|---|
| `cp .env.example .env` | Create Docker Compose configuration. |
| `mkdir -p .rh-mcp-state` | Create local state storage. |
| `docker compose build` | Build the local bridge image. |
| `docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth` | Run browser-based OAuth login. |
| `docker compose up -d` | Start the local bridge in the background. |
| `docker compose ps robinhood-mcp` | Show bridge container status. |
| `docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready` | Run status, tool-list, and smoke checks from the running container. |
| `docker compose exec -T robinhood-mcp robinhood-mcp-bridge status` | Print bridge status from the running container. |
| `docker compose exec -T robinhood-mcp robinhood-mcp-bridge smoke` | Run the MCP smoke check from the running container. |
| `docker compose down` | Stop the local bridge. |

## Port overrides

Set `MCP_HOST_PORT=8081` in `.env` if host port `8080` is already in use. Then run `make url` to print the updated client-facing endpoint.
For a one-off first setup, use `MCP_HOST_PORT=8081 make bootstrap`.
For later starts, use `MCP_HOST_PORT=8081 make start`.
Use the `make url` output for external MCP clients. Docker smoke checks may use the container-local endpoint internally.

Set `AUTH_HOST_PORT=8766` in `.env` if host port `8765` is already in use. Then run `make bootstrap` for first setup or `make auth` for reauthentication; both derive the matching `AUTH_REDIRECT_URI` unless you set one explicitly.
For a one-off login, use `AUTH_HOST_PORT=8766 make auth`.
Leave `AUTH_REDIRECT_URI` commented for the standard local callback flow.
`rh-mcp auth login` is still accepted as a compatibility alias for `rh-mcp auth`.

## State reset

`make reset-state` removes saved OAuth tokens, cached schemas, and local audit logs under `.rh-mcp-state/`. Run `make bootstrap` again afterward.
