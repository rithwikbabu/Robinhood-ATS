from pathlib import Path

from robinhood_mcp_bridge.tools import SUPPORTED_TOOLS


ROOT = Path(__file__).resolve().parents[1]


def test_sdk_reference_mentions_every_supported_tool():
    reference = (ROOT / "docs" / "sdk-reference.md").read_text(encoding="utf-8")
    for tool in SUPPORTED_TOOLS:
        assert f"`{tool}`" in reference


def test_readme_mentions_distribution_import_and_cli_names():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "`robinhood-mcp-bridge`" in readme
    assert "`robinhood_mcp_bridge`" in readme
    assert "`rh-mcp`" in readme
    assert "One-command Docker-first setup" in readme
    assert "For a released package" in readme
    assert "pip install robinhood-mcp-bridge" in readme
    assert "rh-mcp auth" in readme
    assert "rh-mcp serve" in readme
    assert "rh-mcp ready" in readme
    assert "Use `python -m robinhood_mcp_bridge ...`" in readme
    assert "full Python CLI command list" in readme
    assert "rh-mcp init --force" not in readme


def test_readme_sdk_examples_use_default_client_and_explain_overrides():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "client = RobinhoodMCPClient()" in readme
    assert 'RobinhoodMCPClient("http://127.0.0.1:8080/mcp")' not in readme
    assert "pass the URL printed by `make url`" in readme
    assert "bearer_token=..." in readme


def test_readme_badges_link_to_project_assets():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "](pyproject.toml)" in readme
    assert "](LICENSE)" in readme
    assert "actions/workflows/ci.yml/badge.svg" in readme


def test_readme_documents_trading_safety_flags():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "DRY_RUN=true" in readme
    assert "LIVE_TRADING=false" in readme
    assert "DRY_RUN=false" in readme
    assert "LIVE_TRADING=true" in readme
    assert "review_equity_order" in readme
    assert "place_equity_order" in readme


def test_readme_warns_reset_state_removes_local_auth_state():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "make reset-state" in readme
    assert "removes saved OAuth tokens" in readme
    assert "then `make bootstrap`" in readme
    assert "`No upstream OAuth token`: run `make bootstrap`" in readme
    assert "If the bridge is not running, check `make ps`, then start it with `make start`." in readme


def test_readme_mentions_core_make_quickstart_commands():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/quickstart.md" in readme
    assert "docs/commands.md" in readme
    assert "Plain `make` prints the command help" in readme
    for command in [
        "make bootstrap",
        "make stop",
        "make ps",
        "make ready",
        "make smoke",
    ]:
        assert command in readme


def test_readme_points_python_only_users_to_command_reference():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "For local Python-only development, use the `rh-mcp` commands in [docs/commands.md](docs/commands.md)." in readme
    assert "Python-only local smoke path" not in readme


def test_quickstart_documents_minimum_first_run_path():
    quickstart = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
    assert "make bootstrap" in quickstart
    assert "make start" in quickstart
    assert "make stop" in quickstart
    assert "make ps" in quickstart
    assert "make ready" in quickstart
    assert "make url" in quickstart
    assert "http://127.0.0.1:8080/mcp" in quickstart
    assert "`8080`: local MCP bridge" in quickstart
    assert "MCP_HOST_PORT=8081" in quickstart
    assert "MCP_HOST_PORT=8081 make bootstrap" in quickstart
    assert "MCP_HOST_PORT=8081 make start" in quickstart
    assert "`8765`: OAuth callback" in quickstart
    assert "AUTH_HOST_PORT=8766" in quickstart
    assert "AUTH_HOST_PORT=8766 make auth" in quickstart
    assert "does not read accounts" in quickstart
    assert "browser-based Robinhood MCP OAuth login" in quickstart
    assert "`make ready` tolerates brief startup lag" in quickstart
    assert "`make start` also prints the endpoint" in quickstart
    assert "docker compose up -d" in quickstart
    assert "docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready" in quickstart


def test_command_reference_documents_primary_docker_and_python_commands():
    commands = (ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
    for expected in [
        "make init",
        "Print concise command help and a link to this reference",
        "make bootstrap",
        "make auth",
        "make start",
        "Start the local MCP bridge in the background and print its endpoint",
        "make doctor",
        "make ready",
        "make smoke",
        "make stop",
        "rh-mcp auth",
        "rh-mcp serve",
        "rh-mcp ready",
        "rh-mcp smoke",
        "`rh-mcp serve` runs in the foreground",
        "docker compose build",
        "docker compose up -d",
        "docker compose ps robinhood-mcp",
        "docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready",
        "docker compose exec -T robinhood-mcp robinhood-mcp-bridge smoke",
        "docker compose down",
        "MCP_HOST_PORT=8081",
        "MCP_HOST_PORT=8081 make bootstrap",
        "MCP_HOST_PORT=8081 make start",
        "Use the `make url` output for external MCP clients",
        "AUTH_HOST_PORT=8766",
        "AUTH_HOST_PORT=8766 make auth",
        "make bootstrap` for first setup or `make auth` for reauthentication",
        "removes saved OAuth tokens",
        "Run `make bootstrap` again afterward",
    ]:
        assert expected in commands


def test_examples_readme_documents_read_only_boundary():
    examples_readme = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")
    assert "read-only" in examples_readme
    assert "do not review orders, place orders, cancel orders" in examples_readme
    assert "make bootstrap" in examples_readme
    assert "make ready" not in examples_readme
    assert "make start" not in examples_readme
    assert "ROBINHOOD_MCP_BRIDGE_URL" in examples_readme
    assert "LOCAL_MCP_BEARER_TOKEN" in examples_readme


def test_examples_honor_configurable_bridge_url_and_local_bearer_token():
    for path in [
        ROOT / "examples" / "quickstart.py",
        ROOT / "examples" / "read_only.py",
    ]:
        source = path.read_text(encoding="utf-8")
        assert "ROBINHOOD_MCP_BRIDGE_URL" in source
        assert "LOCAL_MCP_BEARER_TOKEN" in source


def test_readme_contents_links_command_reference():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "[Command reference](docs/commands.md)" in readme


def test_quickstart_no_make_path_authenticates_before_starting_bridge():
    quickstart = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
    build = quickstart.index("docker compose build")
    auth = quickstart.index("docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth")
    start = quickstart.index("docker compose up -d")
    ready = quickstart.index("docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready")
    assert build < auth < start < ready


def test_readme_no_make_path_authenticates_before_starting_bridge():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    build = readme.index("docker compose build")
    auth = readme.index("docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth")
    start = readme.index("docker compose up -d")
    ready = readme.index("docker compose exec -T robinhood-mcp robinhood-mcp-bridge ready")
    assert build < auth < start < ready


def test_docs_do_not_use_stale_service_ports_auth_command():
    for path in [
        ROOT / "README.md",
        ROOT / "docs" / "configuration.md",
        ROOT / "docs" / "quickstart.md",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "--service-ports" not in text


def test_quickstart_make_path_bootstrap_starts_before_ready():
    quickstart = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
    bootstrap = quickstart.index("make bootstrap")
    ready = quickstart.index("make ready")
    assert bootstrap < ready
    assert "starts the local bridge, and runs the readiness check" in quickstart
    assert "`make bootstrap` already runs `make ready`" in quickstart


def test_readme_make_path_bootstrap_starts_before_ready():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    bootstrap = readme.index("make bootstrap")
    ready = readme.index("make ready")
    assert bootstrap < ready
    assert "opens a browser-based Robinhood OAuth login, starts the bridge, and checks it" in readme
    assert "`make bootstrap` starts the bridge, prints the endpoint, and runs the readiness check" in readme


def test_readme_documents_minimum_requirements():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Minimum requirements" in readme
    assert "Docker" in readme
    assert "Docker Compose" in readme
    assert "Python 3.11+" in readme
    assert "The `.env` file is for Docker Compose" in readme
    assert "No `make` installed: use the raw Docker Compose sequence in [Quick start](#quick-start)." in readme


def test_readme_documents_loopback_only_default():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "host loopback" in readme
    assert "127.0.0.1:8080" in readme
    assert "MCP_HOST_PORT=8081" in readme
    assert "MCP_HOST_PORT=8081 make bootstrap" in readme
    assert "MCP_HOST_PORT=8081 make start" in readme
    assert "AUTH_HOST_PORT=8766" in readme
    assert "AUTH_HOST_PORT=8766 make auth" in readme
    assert "then run `make bootstrap`" in readme


def test_faq_points_sdk_users_to_bootstrap_flow():
    faq = (ROOT / "docs" / "faq.md").read_text(encoding="utf-8")
    assert "Run `make bootstrap`" in faq
    assert "Authenticate with `make auth`, start the bridge with `make start`" not in faq


def test_env_example_exposes_oauth_redirect_uri():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "MCP_HOST_PORT=8080" in env_example
    assert "AUTH_HOST_PORT=8765" in env_example
    assert "# AUTH_REDIRECT_URI=http://127.0.0.1:8765/callback" in env_example
    assert "STATE_DIR=" not in env_example
    assert "AUDIT_LOG_PATH=" not in env_example


def test_configuration_doc_distinguishes_docker_and_python_ports():
    config_doc = (ROOT / "docs" / "configuration.md").read_text(encoding="utf-8")
    assert "`MCP_HOST_PORT`" in config_doc
    assert "`HOST`" in config_doc
    assert "`PORT`" in config_doc
    assert "prefer `MCP_HOST_PORT` instead of `PORT`" in config_doc
    assert "Docker stores OAuth tokens, cached schemas, and audit logs in `.rh-mcp-state/`" in config_doc
    assert "`STATE_DIR`" in config_doc
    assert "`AUDIT_LOG_PATH`" in config_doc
    assert "Leave `AUTH_REDIRECT_URI` commented" in config_doc
    assert "AUTH_CALLBACK_PORT=8766 AUTH_REDIRECT_URI=http://127.0.0.1:8766/callback rh-mcp auth" in config_doc
    commands_doc = (ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
    assert "`rh-mcp auth login` is still accepted" in commands_doc


def test_testing_doc_explains_smoke_is_non_trading():
    testing_doc = (ROOT / "docs" / "testing.md").read_text(encoding="utf-8")
    assert "Run after `make bootstrap` or `make start`, with the bridge running" in testing_doc
    assert "retries briefly to tolerate startup lag" in testing_doc
    assert "make ready" in testing_doc
    assert "make smoke" in testing_doc
    assert "does not read accounts" in testing_doc
    assert "place orders" in testing_doc
    assert "cancel orders" in testing_doc


def test_mcp_client_doc_mentions_endpoint_and_bearer_config():
    mcp_doc = (ROOT / "docs" / "mcp-clients.md").read_text(encoding="utf-8")
    assert "http://127.0.0.1:8080/mcp" in mcp_doc
    assert "make bootstrap" in mcp_doc
    assert "make url" in mcp_doc
    assert "rh-mcp url" in mcp_doc
    assert "MCP_HOST_PORT" in mcp_doc
    assert "streamable-http" in mcp_doc
    assert "LOCAL_MCP_BEARER_TOKEN" in mcp_doc
    assert "Authorization" in mcp_doc
