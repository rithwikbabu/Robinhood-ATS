# Contributing

This project is intentionally small. Prefer changes that make setup, safety, and MCP interoperability simpler.

## Local development

Docker-first setup:

```bash
make
make bootstrap
```

Python test setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
```

## Design rules

- Use Robinhood's official Agentic Trading MCP only.
- Do not add private Robinhood web or mobile API integrations.
- Keep `place_equity_order` guarded by review, dry-run, live-trading, and configured risk limits.
- Keep upstream MCP schemas authoritative; do not invent alternate local schemas.
- Keep the SDK as a thin MCP convenience client; do not add portfolio analysis, trading strategies, or account-state abstractions.
- Avoid dependencies unless they materially reduce setup or maintenance burden.

See `docs/architecture.md` for the package boundaries.

## Pull requests

- Include tests for changed behavior.
- Do not include account numbers, tokens, audit logs, screenshots with balances, or `.rh-mcp-state` contents.
- Keep docs short enough that a new user can start in minutes.
