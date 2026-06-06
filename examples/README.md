# Examples

These examples are read-only unless a file explicitly says otherwise.

They assume the local bridge is already running:

```bash
make bootstrap
```

If you changed the bridge port, set `ROBINHOOD_MCP_BRIDGE_URL` to the value from `make url`.
If you set `LOCAL_MCP_BEARER_TOKEN`, the examples use it automatically.

## Python SDK examples

```bash
python examples/quickstart.py
python examples/read_only.py
```

The bundled examples do not review orders, place orders, cancel orders, or mutate account state.

## MCP client configs

- `mcp-client-config.json`: basic Streamable HTTP config.
- `mcp-client-config-with-token.json`: config shape for `LOCAL_MCP_BEARER_TOKEN`.

Print the local endpoint with:

```bash
make url
```
