# MCP Client Setup

Set up and start the local bridge first:

```bash
make bootstrap
```

Use this Streamable HTTP endpoint:

```bash
make url
```

If you installed the Python package instead:

```bash
rh-mcp url
```

Default value: `http://127.0.0.1:8080/mcp`

If you changed `MCP_HOST_PORT` in `.env`, rerun `make url` and use the printed endpoint in your MCP client config.

## Basic config

Use `examples/mcp-client-config.json`:

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

## Config with local bearer token

If you set `LOCAL_MCP_BEARER_TOKEN`, use `examples/mcp-client-config-with-token.json`:

```json
{
  "mcpServers": {
    "robinhood": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${LOCAL_MCP_BEARER_TOKEN}"
      }
    }
  }
}
```

Built-in checks such as `make ready` and `make smoke` use this token automatically.

Only expose the bridge beyond localhost if you also provide transport security and a strong bearer token.
