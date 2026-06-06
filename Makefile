.DEFAULT_GOAL := help

.PHONY: help setup-files init bootstrap start stop ps ready url install test check clean build-package logs auth doctor status tools smoke reset-state

help:
	@echo "Common commands:"
	@echo "  make bootstrap     First-time setup: authenticate, start, check"
	@echo "  make url           Print the local MCP endpoint"
	@echo "  make ready         Re-check the running bridge"
	@echo "  make logs          Follow bridge logs"
	@echo "  make start         Restart the bridge"
	@echo "  make stop          Stop the bridge"
	@echo "  make reset-state   Remove saved local OAuth/schema/audit state"
	@echo "More commands: docs/commands.md"

setup-files:
	@test -f .env || cp .env.example .env
	@mkdir -p .rh-mcp-state

init: setup-files
	@echo "Ready. Edit .env if needed, then run: make bootstrap"

bootstrap:
	@RH_MCP_SUPPRESS_AUTH_NEXT_STEP=1 $(MAKE) --no-print-directory auth
	@$(MAKE) --no-print-directory start
	@$(MAKE) --no-print-directory ready

start: setup-files
	docker compose up -d
	@printf "Endpoint: "
	@$(MAKE) --no-print-directory url
	@echo "Bridge starting. Check it with: make ready"

stop:
	docker compose down

ps:
	docker compose ps robinhood-mcp

ready: setup-files
	docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready

url:
	@env_port=$$(printf '%s\n' "$${MCP_HOST_PORT:-}" | sed -n 's/^[[:space:]]*\([0-9][0-9]*\).*$$/\1/p'); file_port=$$(sed -n 's/^[[:space:]]*MCP_HOST_PORT[[:space:]]*=[[:space:]]*\([0-9][0-9]*\).*$$/\1/p' .env 2>/dev/null | tail -n 1); port=$${env_port:-$${file_port}}; echo "http://127.0.0.1:$${port:-8080}/mcp"

install:
	pip install -e ".[dev]"

test:
	pytest

check:
	python -m robinhood_mcp_bridge --version
	python -m robinhood_mcp_bridge tools
	pytest
	docker compose build

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

build-package:
	python -m build

auth: setup-files
	@env_host_port=$$(printf '%s\n' "$${AUTH_HOST_PORT:-}" | sed -n 's/^[[:space:]]*\([0-9][0-9]*\).*$$/\1/p'); file_host_port=$$(sed -n 's/^[[:space:]]*AUTH_HOST_PORT[[:space:]]*=[[:space:]]*\([0-9][0-9]*\).*$$/\1/p' .env 2>/dev/null | tail -n 1); host_port=$${env_host_port:-$${file_host_port}}; env_redirect_uri=$${AUTH_REDIRECT_URI:-}; file_redirect_uri=$$(sed -n 's/^[[:space:]]*AUTH_REDIRECT_URI[[:space:]]*=[[:space:]]*//p' .env 2>/dev/null | tail -n 1); redirect_uri=$${env_redirect_uri:-$${file_redirect_uri}}; AUTH_REDIRECT_URI=$${redirect_uri:-http://127.0.0.1:$${host_port:-8765}/callback} docker compose run --build --rm --publish 127.0.0.1:$${host_port:-8765}:8765 --env RH_MCP_SUPPRESS_AUTH_NEXT_STEP robinhood-mcp auth

logs:
	docker compose logs -f robinhood-mcp

doctor: setup-files
	@docker compose version >/dev/null
	docker compose run --build --rm robinhood-mcp doctor

status: setup-files
	docker compose run --build --rm robinhood-mcp status

tools: setup-files
	docker compose run --build --rm robinhood-mcp tools

smoke: setup-files
	docker compose exec -T robinhood-mcp robinhood-mcp-bridge smoke

reset-state:
	rm -rf .rh-mcp-state
	mkdir -p .rh-mcp-state
	@echo "Local OAuth/schema/audit state reset. Run: make bootstrap"
