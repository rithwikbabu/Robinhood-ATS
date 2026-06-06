from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_makefile_defaults_to_help():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert ".DEFAULT_GOAL := help" in makefile


def test_makefile_contains_documented_quickstart_targets():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in [
        "help:",
        "setup-files:",
        "init:",
        "bootstrap:",
        "start:",
        "stop:",
        "ps:",
        "ready:",
        "url:",
        "auth:",
        "smoke:",
        "doctor:",
        "status:",
        "tools:",
        "reset-state:",
    ]:
        assert target in makefile


def test_make_reset_state_returns_to_bootstrap_flow():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "Local OAuth/schema/audit state reset. Run: make bootstrap" in makefile


def test_make_help_prefers_primary_workflow_over_legacy_aliases():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    help_block = makefile.split("init:", 1)[0]
    assert "make bootstrap" in help_block
    assert "make start" in help_block
    assert "make stop" in help_block
    assert "make ready" in help_block
    assert "docs/commands.md" in help_block
    assert "make init" not in help_block
    assert "make auth" not in help_block
    assert "make doctor" not in help_block
    assert "make smoke" not in help_block
    assert "make ps" not in help_block
    assert "make docker-up" not in help_block
    assert "make docker-down" not in help_block
    assert "make test" not in help_block
    assert "make check" not in help_block
    assert "make build-package" not in help_block


def test_makefile_removes_legacy_docker_aliases():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "docker-build:" not in makefile
    assert "docker-up:" not in makefile
    assert "docker-down:" not in makefile


def test_make_init_guidance_does_not_reinvoke_bootstrap():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "init: setup-files" in makefile
    assert "make bootstrap" in makefile
    assert "make auth && make start" not in makefile
    assert "make bootstrap && make start" not in makefile


def test_make_start_runs_bridge_in_background():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "start: setup-files" in makefile
    assert "docker compose up -d" in makefile
    assert 'printf "Endpoint: "' in makefile
    assert "$(MAKE) --no-print-directory url" in makefile
    assert "Bridge starting. Check it with: make ready" in makefile


def test_make_bootstrap_authenticates_and_starts_bridge():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "bootstrap:" in makefile
    assert "RH_MCP_SUPPRESS_AUTH_NEXT_STEP=1" in makefile
    assert "$(MAKE) --no-print-directory auth" in makefile
    assert "$(MAKE) --no-print-directory start" in makefile
    assert "$(MAKE) --no-print-directory ready" in makefile
    assert "First-time setup: authenticate, start, check" in makefile


def test_make_auth_builds_and_publishes_oauth_callback_port():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "auth: setup-files" in makefile
    assert "AUTH_HOST_PORT[[:space:]]*=" in makefile
    assert "AUTH_REDIRECT_URI[[:space:]]*=" in makefile
    assert 'printf \'%s\\n\' "$${AUTH_HOST_PORT:-}"' in makefile
    assert "env_redirect_uri=$${AUTH_REDIRECT_URI:-}" in makefile
    assert "http://127.0.0.1:$${host_port:-8765}/callback" in makefile
    assert r"\([0-9][0-9]*\)" in makefile
    assert "$${host_port:-8765}:8765" in makefile
    assert "docker compose run --build --rm --publish" in makefile
    assert "--env RH_MCP_SUPPRESS_AUTH_NEXT_STEP" in makefile
    assert "robinhood-mcp auth" in makefile
    assert "robinhood-mcp auth login" not in makefile
    assert "Authenticated. Start the bridge with: make start" not in makefile


def test_make_ready_runs_status_tools_and_smoke():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "ready: setup-files" in makefile
    assert "docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready" in makefile


def test_make_smoke_uses_container_local_default_url():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "smoke: setup-files" in makefile
    assert "docker compose exec -T robinhood-mcp robinhood-mcp-bridge smoke" in makefile
    assert "smoke --url http://127.0.0.1:8080/mcp" not in makefile


def test_make_stop_stops_compose_bridge():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "stop:" in makefile
    assert "docker compose down" in makefile


def test_make_ps_shows_bridge_container_status():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "ps:" in makefile
    assert "docker compose ps robinhood-mcp" in makefile


def test_make_doctor_checks_docker_compose_available():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "doctor: setup-files" in makefile
    assert "docker compose version >/dev/null" in makefile


def test_make_url_uses_configured_mcp_host_port():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "MCP_HOST_PORT[[:space:]]*=" in makefile
    assert 'printf \'%s\\n\' "$${MCP_HOST_PORT:-}"' in makefile
    assert r"\([0-9][0-9]*\)" in makefile
    assert "$${port:-8080}" in makefile
    assert ". ./.env" not in makefile
