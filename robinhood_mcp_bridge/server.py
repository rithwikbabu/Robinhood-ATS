from __future__ import annotations

import logging
import secrets
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from . import __version__
from .audit import AuditLogger
from .auth import AuthRequiredError, OAuthManager
from .config import Settings
from .guardrails import ALLOWED_TOOLS, GuardrailEngine, ReviewCache
from .mcp import is_tool_error_response, jsonrpc_error, jsonrpc_result, tool_text_result
from .state import StateStore
from .upstream import UpstreamError, UpstreamMCPClient


LOG = logging.getLogger("robinhood_mcp_bridge")


class BridgeService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = StateStore(settings.state_dir)
        self.auth = OAuthManager(settings)
        self.upstream = UpstreamMCPClient(settings, self.auth)
        self.audit = AuditLogger(settings.audit_log_path)
        self.review_cache = ReviewCache(ttl_seconds=60)
        self.guardrails = GuardrailEngine(settings, self.review_cache)
        self._tools_by_name: dict[str, dict[str, Any]] = {}

    async def warm_up(self) -> None:
        try:
            await self.load_allowed_tools(force=True)
            LOG.info("Loaded upstream Robinhood MCP tool schemas")
        except AuthRequiredError as exc:
            LOG.warning("Robinhood MCP auth required before tools can be loaded: %s", exc)
        except Exception as exc:
            LOG.warning("Could not load upstream tools during startup: %s", exc)

    async def load_allowed_tools(self, *, force: bool = False) -> list[dict[str, Any]]:
        if self._tools_by_name and not force:
            return list(self._tools_by_name.values())

        upstream_response = await self.upstream.jsonrpc(
            method="tools/list",
            params={},
            request_id=f"tools-list-{secrets.token_hex(8)}",
        )
        if "error" in upstream_response:
            raise UpstreamError(str(upstream_response["error"]))
        result = upstream_response.get("result") or {}
        tools = result.get("tools") or []
        allowed = [
            tool for tool in tools
            if isinstance(tool, dict) and tool.get("name") in ALLOWED_TOOLS
        ]
        self._tools_by_name = {str(tool["name"]): tool for tool in allowed}
        self.store.write_json("tools_cache.json", {"tools": allowed})
        return allowed

    def cached_tools(self) -> list[dict[str, Any]]:
        if self._tools_by_name:
            return list(self._tools_by_name.values())
        cached = self.store.read_json("tools_cache.json")
        if cached and isinstance(cached.get("tools"), list):
            tools = [
                tool for tool in cached["tools"]
                if isinstance(tool, dict) and tool.get("name") in ALLOWED_TOOLS
            ]
            self._tools_by_name = {str(tool["name"]): tool for tool in tools}
            return tools
        return []

    async def dispatch(self, message: dict[str, Any], client_id: str) -> dict[str, Any] | None:
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}

        if method == "initialize":
            return jsonrpc_result(
                request_id,
                {
                    "protocolVersion": self.settings.mcp_protocol_version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "robinhood-mcp-bridge",
                        "version": __version__,
                    },
                    "instructions": (
                        "Local guarded MCP bridge to Robinhood Agentic Trading. "
                        "Only equity/account tools are exposed. Real order placement "
                        "requires review_equity_order, DRY_RUN=false, and LIVE_TRADING=true."
                    ),
                },
            )

        if method == "notifications/initialized":
            return None

        if method == "ping":
            return jsonrpc_result(request_id, {})

        if method == "tools/list":
            return await self.handle_tools_list(request_id)

        if method == "tools/call":
            if not isinstance(params, dict):
                return jsonrpc_error(request_id, -32602, "tools/call params must be an object")
            return await self.handle_tools_call(request_id, params, client_id)

        return jsonrpc_error(request_id, -32601, f"Method not found: {method}")

    async def handle_tools_list(self, request_id: Any) -> dict[str, Any]:
        try:
            tools = await self.load_allowed_tools()
        except AuthRequiredError as exc:
            tools = self.cached_tools()
            if not tools:
                return jsonrpc_error(request_id, -32040, str(exc))
        except Exception as exc:
            tools = self.cached_tools()
            if not tools:
                return jsonrpc_error(request_id, -32050, f"Could not load upstream tools: {exc}")
        return jsonrpc_result(
            request_id,
            {
                "resultType": "complete",
                "tools": tools,
                "ttlMs": 300000,
                "cacheScope": "private",
            },
        )

    async def handle_tools_call(
        self,
        request_id: Any,
        params: dict[str, Any],
        client_id: str,
    ) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        request_id_text = str(request_id or secrets.token_hex(8))

        if not isinstance(name, str):
            return jsonrpc_error(request_id, -32602, "tools/call params.name must be a string")
        if not isinstance(arguments, dict):
            return jsonrpc_error(request_id, -32602, "tools/call params.arguments must be an object")
        if name not in ALLOWED_TOOLS:
            self.audit.log_tool_call(
                request_id=request_id_text,
                client_id=client_id,
                tool_name=name,
                arguments=arguments,
                decision="blocked_tool_not_allowlisted",
            )
            return jsonrpc_result(
                request_id,
                tool_text_result(
                    f"Tool {name!r} is not exposed by this bridge.",
                    is_error=True,
                    structured={"reason": "tool_not_allowlisted"},
                ),
            )

        if name == "place_equity_order":
            decision = await self.guardrails.validate_place(client_id=client_id, arguments=arguments)
            if not decision.allowed:
                self.audit.log_tool_call(
                    request_id=request_id_text,
                    client_id=client_id,
                    tool_name=name,
                    arguments=arguments,
                    decision=f"blocked_{decision.reason}",
                )
                return jsonrpc_result(
                    request_id,
                    tool_text_result(
                        f"place_equity_order blocked: {decision.reason}",
                        is_error=True,
                        structured=decision.details,
                    ),
                )
            if self.settings.dry_run:
                self.audit.log_tool_call(
                    request_id=request_id_text,
                    client_id=client_id,
                    tool_name=name,
                    arguments=arguments,
                    decision="dry_run_not_forwarded",
                )
                return jsonrpc_result(
                    request_id,
                    tool_text_result(
                        "Dry-run: place_equity_order was not forwarded to Robinhood.",
                        structured={
                            "dry_run": True,
                            "forwarded": False,
                            "guardrails": decision.details,
                        },
                    ),
                )
            if not self.settings.live_trading:
                self.audit.log_tool_call(
                    request_id=request_id_text,
                    client_id=client_id,
                    tool_name=name,
                    arguments=arguments,
                    decision="blocked_live_trading_disabled",
                )
                return jsonrpc_result(
                    request_id,
                    tool_text_result(
                        "LIVE_TRADING must be true before real orders are forwarded.",
                        is_error=True,
                        structured={"live_trading": False},
                    ),
                )

        try:
            await self.load_allowed_tools()
            tool_schema = self._tools_by_name.get(name)
            upstream_response = await self.upstream.jsonrpc(
                method="tools/call",
                params={"name": name, "arguments": arguments},
                request_id=f"tool-call-{secrets.token_hex(8)}",
                tool_schema=tool_schema,
            )
        except AuthRequiredError as exc:
            self.audit.log_tool_call(
                request_id=request_id_text,
                client_id=client_id,
                tool_name=name,
                arguments=arguments,
                decision="blocked_upstream_auth_required",
                error=str(exc),
            )
            return jsonrpc_error(request_id, -32040, str(exc))
        except UpstreamError as exc:
            self.audit.log_tool_call(
                request_id=request_id_text,
                client_id=client_id,
                tool_name=name,
                arguments=arguments,
                decision="upstream_http_error",
                upstream_status=exc.status_code,
                error=str(exc),
            )
            return jsonrpc_error(request_id, -32050, str(exc))

        if "error" in upstream_response:
            self.audit.log_tool_call(
                request_id=request_id_text,
                client_id=client_id,
                tool_name=name,
                arguments=arguments,
                decision="upstream_jsonrpc_error",
                upstream_status=self.upstream.last_status_code,
                result=upstream_response,
            )
            upstream_error = upstream_response["error"]
            return jsonrpc_error(
                request_id,
                upstream_error.get("code", -32050),
                upstream_error.get("message", "Upstream error"),
                upstream_error.get("data"),
            )

        if name == "review_equity_order" and not is_tool_error_response(upstream_response):
            await self.review_cache.record(client_id, arguments)

        self.audit.log_tool_call(
            request_id=request_id_text,
            client_id=client_id,
            tool_name=name,
            arguments=arguments,
            decision="forwarded",
            upstream_status=self.upstream.last_status_code,
            result=upstream_response.get("result"),
        )
        return jsonrpc_result(request_id, upstream_response.get("result"))


def local_client_id(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth:
        return auth
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "local"


def check_local_auth(request: Request, settings: Settings) -> JSONResponse | None:
    expected = settings.local_mcp_bearer_token
    if not expected:
        return None
    actual = request.headers.get("authorization", "")
    if actual != f"Bearer {expected}":
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return None


async def mcp_endpoint(request: Request) -> Response:
    service: BridgeService = request.app.state.bridge
    auth_error = check_local_auth(request, service.settings)
    if auth_error:
        return auth_error
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(jsonrpc_error(None, -32700, "Parse error"), status_code=400)

    client_id = local_client_id(request)

    async def handle_one(message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return jsonrpc_error(None, -32600, "Invalid Request")
        try:
            return await service.dispatch(message, client_id)
        except Exception as exc:
            LOG.exception("Unhandled MCP bridge error")
            return jsonrpc_error(message.get("id"), -32603, "Internal error", {"detail": str(exc)})

    if isinstance(payload, list):
        responses = [response for response in [await handle_one(item) for item in payload] if response]
        if not responses:
            return Response(status_code=202)
        return JSONResponse(responses)

    response = await handle_one(payload)
    if response is None:
        return Response(status_code=202)
    return JSONResponse(response)


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "service": "robinhood-mcp-bridge", "version": __version__})


def create_app(settings: Settings | None = None) -> Starlette:
    settings = settings or Settings.from_env()
    settings.ensure_state_dirs()
    bridge = BridgeService(settings)

    async def lifespan(app: Starlette):
        app.state.bridge = bridge
        await bridge.warm_up()
        yield

    return Starlette(
        debug=False,
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/mcp", mcp_endpoint, methods=["POST"]),
        ],
        lifespan=lifespan,
    )
