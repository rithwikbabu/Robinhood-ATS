# Release Checklist

Keep releases small and boring.

1. Update `version` in `pyproject.toml` and `robinhood_mcp_bridge/__init__.py`.
2. Update `CHANGELOG.md`.
3. Run `pip install -e ".[dev]"`.
4. Run `make check`.
5. Dry-run the Docker-first docs flow on a clean checkout: `make`, `make bootstrap`, `make ps`, then `make stop`.
6. Confirm `README.md`, `docs/quickstart.md`, and `docs/commands.md` still match the current package.
7. Check that new dependencies are necessary and documented.
8. Build distributions with `make build-package`.
9. Install publishing tools only when needed, for example `python -m pip install twine`.
10. Publish only if no tokens, account numbers, audit logs, or `.rh-mcp-state` files are present.
