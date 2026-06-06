from __future__ import annotations

from pathlib import Path

from robinhood_mcp_bridge import cli
from robinhood_mcp_bridge.config import Settings
from robinhood_mcp_bridge.sdk import RobinhoodMCPError
from robinhood_mcp_bridge.tools import SUPPORTED_TOOLS


class FakeClient:
    instances = []

    def __init__(self, url, *, bearer_token=None):
        self.url = url
        self.bearer_token = bearer_token
        self.instances.append(self)

    def initialize(self):
        return {"serverInfo": {"name": "test"}}

    def list_tools(self):
        return [{"name": name} for name in SUPPORTED_TOOLS]

    def call_tool(self, name, **arguments):
        raise AssertionError("smoke must not call tools")


class AuthRequiredClient(FakeClient):
    def list_tools(self):
        raise RobinhoodMCPError(-32040, "No upstream OAuth token")


class UpstreamErrorClient(FakeClient):
    def list_tools(self):
        raise RobinhoodMCPError(-32050, "Could not load upstream tools")


class UnreachableClient(FakeClient):
    def initialize(self):
        raise OSError("connection refused")


class FlakyClient(FakeClient):
    attempts = 0

    def initialize(self):
        self.__class__.attempts += 1
        if self.__class__.attempts == 1:
            raise OSError("connection refused")
        return {"serverInfo": {"name": "test"}}


def test_smoke_only_checks_handshake_and_tools(monkeypatch, capsys):
    FakeClient.instances = []
    monkeypatch.setattr(cli, "RobinhoodMCPClient", FakeClient)
    cli.run_smoke("http://127.0.0.1:8080/mcp")
    output = capsys.readouterr().out
    assert "expected 22-tool surface is exposed" in output
    assert FakeClient.instances[0].bearer_token is None


def test_smoke_passes_local_bearer_token(monkeypatch, capsys):
    FakeClient.instances = []
    monkeypatch.setattr(cli, "RobinhoodMCPClient", FakeClient)
    cli.run_smoke("http://127.0.0.1:8080/mcp", bearer_token="local-secret")
    output = capsys.readouterr().out
    assert "expected 22-tool surface is exposed" in output
    assert FakeClient.instances[0].bearer_token == "local-secret"


def test_smoke_auth_error_guides_to_auth(monkeypatch, capsys):
    monkeypatch.setattr(cli, "RobinhoodMCPClient", AuthRequiredClient)
    try:
        cli.run_smoke("http://127.0.0.1:8080/mcp")
    except SystemExit as exc:
        assert exc.code == 1
    output = capsys.readouterr().out
    assert "Authenticate first with `make bootstrap` or `rh-mcp auth`" in output
    assert "Start the bridge first" not in output


def test_smoke_non_auth_mcp_error_guides_to_logs(monkeypatch, capsys):
    monkeypatch.setattr(cli, "RobinhoodMCPClient", UpstreamErrorClient)
    try:
        cli.run_smoke("http://127.0.0.1:8080/mcp")
    except SystemExit as exc:
        assert exc.code == 1
    output = capsys.readouterr().out
    assert "Check bridge logs with `make logs`, or inspect the terminal running `rh-mcp serve`" in output
    assert "Start the bridge first" not in output


def test_smoke_unreachable_bridge_mentions_startup_retry(monkeypatch, capsys):
    monkeypatch.setattr(cli, "RobinhoodMCPClient", UnreachableClient)
    try:
        cli.run_smoke("http://127.0.0.1:8080/mcp", attempts=1)
    except SystemExit as exc:
        assert exc.code == 1
    output = capsys.readouterr().out
    assert "Start the bridge first with `make start` or `rh-mcp serve`" in output
    assert "retry this check in a few seconds" in output


def test_smoke_retries_transient_startup_failure(monkeypatch, capsys):
    FlakyClient.attempts = 0
    monkeypatch.setattr(cli, "RobinhoodMCPClient", FlakyClient)
    cli.run_smoke("http://127.0.0.1:8080/mcp", attempts=2, retry_delay_seconds=0)
    output = capsys.readouterr().out
    assert "expected 22-tool surface is exposed" in output
    assert FlakyClient.attempts == 2


def test_tools_command_does_not_parse_runtime_env(monkeypatch, capsys):
    monkeypatch.setenv("PORT", "not-an-int")
    cli.main(["tools"])
    output = capsys.readouterr().out
    assert "Supported Robinhood MCP tools" in output
    assert "get_accounts" in output


def test_init_creates_env_and_state_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    cli.run_init()
    first_output = capsys.readouterr().out

    assert "wrote   .env" in first_output
    assert "ready   .rh-mcp-state/" in first_output
    assert ".env is used by Docker Compose" in first_output
    assert "Python CLI commands read process env" in first_output
    assert "make bootstrap" in first_output
    assert "rh-mcp auth" in first_output
    assert "rh-mcp serve" in first_output
    assert (tmp_path / ".env").exists()
    assert (tmp_path / ".rh-mcp-state").is_dir()
    assert "ROBINHOOD_MCP_URL=https://agent.robinhood.com/mcp/trading" in (tmp_path / ".env").read_text()

    (tmp_path / ".env").write_text("CUSTOM=true\n")
    cli.run_init()

    assert (tmp_path / ".env").read_text() == "CUSTOM=true\n"


def test_embedded_env_template_matches_env_example():
    env_example = (Path(__file__).resolve().parents[1] / ".env.example").read_text(encoding="utf-8")
    assert cli.DEFAULT_ENV_TEMPLATE == env_example


def test_env_template_leaves_redirect_uri_commented_for_auth_port_derivation():
    assert "Change if 8080 is already in use" in cli.DEFAULT_ENV_TEMPLATE
    assert "Change AUTH_HOST_PORT if 8765 is already in use" in cli.DEFAULT_ENV_TEMPLATE
    assert "Leave AUTH_REDIRECT_URI commented" in cli.DEFAULT_ENV_TEMPLATE
    assert "AUTH_HOST_PORT=8765" in cli.DEFAULT_ENV_TEMPLATE
    assert "# AUTH_REDIRECT_URI=http://127.0.0.1:8765/callback" in cli.DEFAULT_ENV_TEMPLATE
    assert "\nAUTH_REDIRECT_URI=http://127.0.0.1:8765/callback" not in cli.DEFAULT_ENV_TEMPLATE
    assert "STATE_DIR=" not in cli.DEFAULT_ENV_TEMPLATE
    assert "AUDIT_LOG_PATH=" not in cli.DEFAULT_ENV_TEMPLATE


def test_url_prints_configured_local_mcp_endpoint(capsys):
    settings = Settings.from_env()
    cli.run_url(settings)
    output = capsys.readouterr().out
    expected_host = "127.0.0.1" if settings.host in {"0.0.0.0", "::", "[::]"} else settings.host
    assert output == f"http://{expected_host}:{settings.port}/mcp\n"


def test_url_prints_loopback_for_public_bind_host(capsys):
    settings = Settings.from_env()
    docker_settings = Settings(**{**settings.__dict__, "host": "0.0.0.0"})
    cli.run_url(docker_settings)
    output = capsys.readouterr().out
    assert output == f"http://127.0.0.1:{settings.port}/mcp\n"


def test_local_mcp_client_url_uses_configured_port_and_loopback_host():
    settings = Settings.from_env()
    custom_settings = Settings(**{**settings.__dict__, "host": "0.0.0.0", "port": 9999})
    assert cli.local_mcp_client_url(custom_settings) == "http://127.0.0.1:9999/mcp"


def test_local_mcp_client_url_uses_docker_host_port_for_public_bind():
    settings = Settings.from_env()
    custom_settings = Settings(
        **{
            **settings.__dict__,
            "host": "0.0.0.0",
            "port": 8080,
            "mcp_host_port": 8081,
        }
    )
    assert cli.local_mcp_client_url(custom_settings) == "http://127.0.0.1:8081/mcp"


def test_local_mcp_runtime_url_uses_container_port_for_public_bind():
    settings = Settings.from_env()
    custom_settings = Settings(
        **{
            **settings.__dict__,
            "host": "0.0.0.0",
            "port": 8080,
            "mcp_host_port": 8081,
        }
    )
    assert cli.local_mcp_runtime_url(custom_settings) == "http://127.0.0.1:8080/mcp"


def test_local_mcp_client_url_brackets_ipv6_hosts():
    settings = Settings.from_env()
    ipv6_settings = Settings(**{**settings.__dict__, "host": "::1", "port": 9999})
    assert cli.local_mcp_client_url(ipv6_settings) == "http://[::1]:9999/mcp"


def test_status_prints_client_facing_local_mcp_url(capsys):
    settings = Settings.from_env()
    docker_settings = Settings(**{**settings.__dict__, "host": "0.0.0.0", "port": 9999})
    cli.run_status(docker_settings)
    output = capsys.readouterr().out
    assert "local_mcp_url: http://127.0.0.1:9999/mcp" in output


def test_doctor_guidance_distinguishes_docker_and_python_paths(tmp_path, capsys):
    settings = Settings.from_env()
    doctor_settings = Settings(
        **{
            **settings.__dict__,
            "state_dir": tmp_path / "missing-state",
            "audit_log_path": tmp_path / "missing-state" / "audit.jsonl",
        }
    )
    try:
        cli.run_doctor(doctor_settings)
    except SystemExit as exc:
        assert exc.code == 1
    output = capsys.readouterr().out
    assert "Docker users run `make bootstrap`" in output
    assert "Python CLI users run `rh-mcp auth`" in output


def test_parser_exposes_ready_command():
    help_text = cli.build_parser().format_help()
    assert "ready" in help_text
    assert "Create Docker .env" in help_text


def test_auth_command_accepts_short_and_compatibility_forms():
    parser = cli.build_parser()
    short = parser.parse_args(["auth"])
    compat = parser.parse_args(["auth", "login"])
    help_text = parser.format_help()
    assert short.command == "auth"
    assert short.auth_command is None
    assert compat.command == "auth"
    assert compat.auth_command == "login"
    assert "Authenticate with Robinhood MCP" in help_text
    assert "Manage upstream Robinhood MCP auth" not in help_text
    assert "Compatibility alias for auth" in Path(cli.__file__).read_text(encoding="utf-8")


def test_auth_login_prints_shared_next_step_guidance():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert "RH_MCP_SUPPRESS_AUTH_NEXT_STEP" in source
    assert "if the bridge is not already running" in source
    assert "start it with `make start` or `rh-mcp serve`" in source
