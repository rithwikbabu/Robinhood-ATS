from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

import uvicorn

from . import __version__
from .auth import OAuthManager
from .config import Settings
from .sdk import RobinhoodMCPClient, RobinhoodMCPError
from .server import create_app
from .tools import ALLOWED_TOOLS


DEFAULT_ENV_TEMPLATE = """# Copy to .env and edit as needed.

ROBINHOOD_MCP_URL=https://agent.robinhood.com/mcp/trading

# Host port for the local MCP bridge. Change if 8080 is already in use.
MCP_HOST_PORT=8080

# Safe by default: reads and reviews forward, real equity order placement does not.
DRY_RUN=true
LIVE_TRADING=false

# Optional trading guardrails.
MAX_ORDER_NOTIONAL_USD=
SYMBOL_ALLOWLIST=
MARKET_HOURS_ONLY=true
ALLOW_FRACTIONAL_EQUITIES=true

# Required only if you expose the local bridge beyond 127.0.0.1.
LOCAL_MCP_BEARER_TOKEN=

# OAuth callback used during browser login. Change AUTH_HOST_PORT if 8765 is already in use.
# Leave AUTH_REDIRECT_URI commented unless you need a custom redirect URI.
AUTH_HOST_PORT=8765
# AUTH_REDIRECT_URI=http://127.0.0.1:8765/callback
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rh-mcp",
        description="Run a local MCP bridge to Robinhood Agentic Trading.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init", help="Create Docker .env and local state directory")
    init.add_argument("--force", action="store_true", help="Overwrite an existing .env")

    serve = subparsers.add_parser("serve", help="Run the local MCP bridge at /mcp")
    serve.add_argument("--host", help="Override HOST")
    serve.add_argument("--port", type=int, help="Override PORT")

    auth = subparsers.add_parser("auth", help="Authenticate with Robinhood MCP")
    auth_sub = auth.add_subparsers(dest="auth_command")
    auth_sub.add_parser("login", help="Compatibility alias for auth")

    subparsers.add_parser("doctor", help="Check local setup without contacting Robinhood")
    subparsers.add_parser("status", help="Print local package/config status")
    subparsers.add_parser("tools", help="List supported Robinhood MCP tools")
    subparsers.add_parser("url", help="Print the local MCP bridge URL")

    ready = subparsers.add_parser("ready", help="Run status, tools, and smoke checks")
    ready.add_argument(
        "--url",
        default=None,
        help="Local MCP bridge URL",
    )

    smoke = subparsers.add_parser("smoke", help="Check the running local MCP bridge")
    smoke.add_argument(
        "--url",
        default=None,
        help="Local MCP bridge URL",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)

    if args.command == "init":
        run_init(force=args.force)
        return

    if args.command == "tools":
        run_tools()
        return

    settings = Settings.from_env()

    if args.command == "serve" or args.command is None:
        host = args.host or settings.host
        port = args.port or settings.port
        settings = Settings(**{**settings.__dict__, "host": host, "port": port})
        settings.validate_bind_safety()
        app = create_app(settings)
        uvicorn.run(app, host=settings.host, port=settings.port)
        return

    if args.command == "auth" and args.auth_command in {None, "login"}:
        settings.ensure_state_dirs()
        asyncio.run(OAuthManager(settings).login())
        if os.getenv("RH_MCP_SUPPRESS_AUTH_NEXT_STEP") != "1":
            print("Next step: if the bridge is not already running, start it with `make start` or `rh-mcp serve`.")
        return

    if args.command == "doctor":
        run_doctor(settings)
        return

    if args.command == "status":
        run_status(settings)
        return

    if args.command == "url":
        run_url(settings)
        return

    if args.command == "ready":
        run_ready(settings, args.url or local_mcp_runtime_url(settings))
        return

    if args.command == "smoke":
        run_smoke(
            args.url or local_mcp_runtime_url(settings),
            bearer_token=settings.local_mcp_bearer_token,
        )
        return

    build_parser().print_help()
    sys.exit(2)


def run_init(force: bool = False) -> None:
    env_path = Path(".env")
    state_dir = Path(".rh-mcp-state")
    template_path = Path(".env.example")

    if env_path.exists() and not force:
        print("exists  .env")
    else:
        env_text = template_path.read_text(encoding="utf-8") if template_path.exists() else DEFAULT_ENV_TEMPLATE
        env_path.write_text(env_text, encoding="utf-8")
        print("wrote   .env")

    state_dir.mkdir(exist_ok=True)
    print("ready   .rh-mcp-state/")
    print("note    .env is used by Docker Compose; Python CLI commands read process env.")
    print("\nNext step:")
    print("  Docker: run `make bootstrap`.")
    print("  Python: run `rh-mcp auth`, then `rh-mcp serve`.")


def run_doctor(settings: Settings) -> None:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("state directory", settings.state_dir.exists(), str(settings.state_dir)))
    checks.append(("oauth discovery", (settings.state_dir / "oauth_discovery.json").exists(), "run `rh-mcp auth` if missing"))
    checks.append(("oauth client", (settings.state_dir / "oauth_client.json").exists(), "run `rh-mcp auth` if missing"))
    checks.append(("oauth tokens", (settings.state_dir / "tokens.json").exists(), "run `rh-mcp auth` if missing"))
    checks.append(("audit log parent", settings.audit_log_path.parent.exists(), str(settings.audit_log_path.parent)))

    try:
        settings.validate_bind_safety()
        checks.append(("bind safety", True, f"HOST={settings.host}"))
    except RuntimeError as exc:
        checks.append(("bind safety", False, str(exc)))

    print("Robinhood MCP Bridge setup check")
    failed = False
    for label, ok, detail in checks:
        status = "ok" if ok else "missing"
        print(f"{status:7} {label}: {detail}")
        failed = failed or not ok

    if failed:
        print("\nNext step: Docker users run `make bootstrap`; Python CLI users run `rh-mcp auth`.")
        sys.exit(1)

    print("\nReady: start the bridge with `make start` or `rh-mcp serve`.")


def run_status(settings: Settings) -> None:
    token_file = settings.state_dir / "tokens.json"
    client_file = settings.state_dir / "oauth_client.json"
    discovery_file = settings.state_dir / "oauth_discovery.json"
    print("Robinhood MCP Bridge")
    print(f"version: {__version__}")
    print(f"local_mcp_url: {local_mcp_client_url(settings)}")
    print(f"upstream_mcp_url: {settings.upstream_url}")
    print(f"state_dir: {settings.state_dir}")
    print(f"audit_log_path: {settings.audit_log_path}")
    print(f"dry_run: {settings.dry_run}")
    print(f"live_trading: {settings.live_trading}")
    print(f"market_hours_only: {settings.market_hours_only}")
    print(f"symbol_allowlist_count: {len(settings.symbol_allowlist)}")
    print(f"oauth_discovery_present: {discovery_file.exists()}")
    print(f"oauth_client_present: {client_file.exists()}")
    print(f"oauth_tokens_present: {token_file.exists()}")


def run_tools() -> None:
    print("Supported Robinhood MCP tools")
    for name in ALLOWED_TOOLS:
        print(name)


def run_url(settings: Settings) -> None:
    print(local_mcp_client_url(settings))


def local_mcp_client_url(settings: Settings) -> str:
    public_bind = settings.host in {"0.0.0.0", "::", "[::]"}
    host = "127.0.0.1" if public_bind else settings.host
    port = settings.mcp_host_port if public_bind and settings.mcp_host_port else settings.port
    return format_local_mcp_url(host, port)


def local_mcp_runtime_url(settings: Settings) -> str:
    host = "127.0.0.1" if settings.host in {"0.0.0.0", "::", "[::]"} else settings.host
    return format_local_mcp_url(host, settings.port)


def format_local_mcp_url(host: str, port: int) -> str:
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{port}/mcp"


def run_ready(settings: Settings, url: str) -> None:
    run_status(settings)
    print()
    run_tools()
    print()
    run_smoke(url, bearer_token=settings.local_mcp_bearer_token)


def run_smoke(
    url: str,
    *,
    bearer_token: str | None = None,
    attempts: int = 5,
    retry_delay_seconds: float = 1.0,
) -> None:
    client = RobinhoodMCPClient(url, bearer_token=bearer_token)
    last_error: Exception | None = None
    attempts = max(1, attempts)
    for attempt in range(1, attempts + 1):
        try:
            info = client.initialize()
            tools = client.list_tools()
            break
        except RobinhoodMCPError as exc:
            print(f"failed  local MCP bridge: {exc.message}")
            if exc.code == -32040:
                print("\nAuthenticate first with `make bootstrap` or `rh-mcp auth`.")
            else:
                print("\nCheck bridge logs with `make logs`, or inspect the terminal running `rh-mcp serve`.")
            sys.exit(1)
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(retry_delay_seconds)
                continue
            print(f"failed  local MCP bridge: {exc}")
            print("\nStart the bridge first with `make start` or `rh-mcp serve`.")
            print("If it just started, retry this check in a few seconds.")
            sys.exit(1)
    else:
        raise AssertionError(f"unreachable smoke retry state: {last_error}")

    names = sorted(tool.get("name") for tool in tools if isinstance(tool, dict))
    expected = sorted(ALLOWED_TOOLS)
    missing = sorted(set(expected) - set(names))
    extra = sorted(set(names) - set(expected))

    print("Robinhood MCP Bridge smoke check")
    print(f"ok      server: {info.get('serverInfo', {}).get('name', 'unknown')}")
    print(f"ok      url: {url}")
    print(f"ok      tools: {len(names)} exposed")

    if missing or extra:
        print(f"failed  missing tools: {missing}")
        print(f"failed  unexpected tools: {extra}")
        sys.exit(1)

    print("ok      expected 22-tool surface is exposed")
