from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None or value.strip() == "":
        return None
    try:
        return Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def parse_symbols(value: str | None) -> frozenset[str]:
    if value is None or value.strip() == "":
        return frozenset()
    return frozenset(part.strip().upper() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    upstream_url: str
    host: str
    port: int
    mcp_protocol_version: str
    state_dir: Path
    audit_log_path: Path
    dry_run: bool
    live_trading: bool
    max_order_notional_usd: Decimal | None
    symbol_allowlist: frozenset[str]
    market_hours_only: bool
    allow_fractional_equities: bool
    local_mcp_bearer_token: str | None
    allow_docker_loopback_bind: bool
    auth_redirect_uri: str
    auth_callback_bind_host: str
    auth_callback_port: int
    oauth_client_id: str | None
    oauth_client_secret: str | None
    request_timeout_seconds: float
    mcp_host_port: int | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        state_dir = Path(os.getenv("STATE_DIR", ".rh-mcp-state"))
        audit_log_path = Path(os.getenv("AUDIT_LOG_PATH", str(state_dir / "audit.jsonl")))
        mcp_host_port = os.getenv("MCP_HOST_PORT")
        return cls(
            upstream_url=os.getenv(
                "ROBINHOOD_MCP_URL",
                "https://agent.robinhood.com/mcp/trading",
            ),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8080")),
            mcp_protocol_version=os.getenv("MCP_PROTOCOL_VERSION", "2025-06-18"),
            state_dir=state_dir,
            audit_log_path=audit_log_path,
            dry_run=parse_bool(os.getenv("DRY_RUN"), default=True),
            live_trading=parse_bool(os.getenv("LIVE_TRADING"), default=False),
            max_order_notional_usd=parse_decimal(os.getenv("MAX_ORDER_NOTIONAL_USD")),
            symbol_allowlist=parse_symbols(os.getenv("SYMBOL_ALLOWLIST")),
            market_hours_only=parse_bool(os.getenv("MARKET_HOURS_ONLY"), default=True),
            allow_fractional_equities=parse_bool(
                os.getenv("ALLOW_FRACTIONAL_EQUITIES"),
                default=True,
            ),
            local_mcp_bearer_token=os.getenv("LOCAL_MCP_BEARER_TOKEN") or None,
            allow_docker_loopback_bind=parse_bool(
                os.getenv("ALLOW_DOCKER_LOOPBACK_BIND"),
                default=False,
            ),
            auth_redirect_uri=os.getenv(
                "AUTH_REDIRECT_URI",
                "http://127.0.0.1:8765/callback",
            ),
            auth_callback_bind_host=os.getenv("AUTH_CALLBACK_BIND_HOST", "127.0.0.1"),
            auth_callback_port=int(os.getenv("AUTH_CALLBACK_PORT", "8765")),
            oauth_client_id=os.getenv("ROBINHOOD_OAUTH_CLIENT_ID") or None,
            oauth_client_secret=os.getenv("ROBINHOOD_OAUTH_CLIENT_SECRET") or None,
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
            mcp_host_port=int(mcp_host_port) if mcp_host_port else None,
        )

    def ensure_state_dirs(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def validate_bind_safety(self) -> None:
        public_bind = self.host in {"0.0.0.0", "::", "[::]"}
        if not public_bind:
            return
        if self.local_mcp_bearer_token:
            return
        if self.allow_docker_loopback_bind:
            return
        raise RuntimeError(
            "Refusing to bind MCP bridge to a public interface without "
            "LOCAL_MCP_BEARER_TOKEN. Use HOST=127.0.0.1 for local runs, or set "
            "LOCAL_MCP_BEARER_TOKEN before exposing the service."
        )
