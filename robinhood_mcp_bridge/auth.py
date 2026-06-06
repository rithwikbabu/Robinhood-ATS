from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import select
import sys
import time
import urllib.parse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import httpx

from .config import Settings
from .state import StateStore


class AuthRequiredError(RuntimeError):
    pass


@dataclass(frozen=True)
class OAuthClient:
    client_id: str
    client_secret: str | None = None


@dataclass(frozen=True)
class OAuthDiscovery:
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str | None
    issuer: str | None
    scopes_supported: list[str]
    resource: str


def parse_www_authenticate(header: str | None) -> dict[str, str]:
    if not header:
        return {}
    value = header.strip()
    if value.lower().startswith("bearer"):
        value = value[6:].strip()
    result: dict[str, str] = {}
    position = 0
    while position < len(value):
        while position < len(value) and value[position] in " ,":
            position += 1
        start = position
        while position < len(value) and value[position] not in " =":
            position += 1
        key = value[start:position]
        while position < len(value) and value[position] == " ":
            position += 1
        if position >= len(value) or value[position] != "=":
            break
        position += 1
        if position < len(value) and value[position] == '"':
            position += 1
            chars: list[str] = []
            while position < len(value):
                char = value[position]
                if char == "\\" and position + 1 < len(value):
                    chars.append(value[position + 1])
                    position += 2
                    continue
                if char == '"':
                    position += 1
                    break
                chars.append(char)
                position += 1
            result[key] = "".join(chars)
        else:
            start = position
            while position < len(value) and value[position] != ",":
                position += 1
            result[key] = value[start:position].strip()
    return result


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def now_epoch() -> int:
    return int(time.time())


class _CallbackHandler(BaseHTTPRequestHandler):
    server: "_CallbackServer"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        self.server.callback_path = self.path
        self.server.callback_params = params
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Robinhood MCP Bridge authenticated</h1>"
            b"<p>You can close this tab and return to the terminal.</p></body></html>"
        )


class _CallbackServer(HTTPServer):
    callback_path: str | None = None
    callback_params: dict[str, str] | None = None


def _parse_manual_callback(text: str) -> dict[str, str] | None:
    text = text.strip()
    if not text:
        return None
    parsed = urllib.parse.urlparse(text)
    if parsed.query:
        return dict(urllib.parse.parse_qsl(parsed.query))
    if text.startswith("code=") or "&code=" in text:
        return dict(urllib.parse.parse_qsl(text))
    return {"code": text}


def wait_for_callback(
    *,
    bind_host: str,
    port: int,
    expected_state: str,
    timeout_seconds: int = 300,
) -> dict[str, str]:
    server = _CallbackServer((bind_host, port), _CallbackHandler)
    server.timeout = 1
    deadline = time.time() + timeout_seconds
    print("Waiting for OAuth callback. If the browser cannot reach the callback URL,")
    print("paste the final redirected URL or the authorization code here and press Enter.")
    while time.time() < deadline:
        server.handle_request()
        if server.callback_params:
            params = server.callback_params
            break
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            manual = _parse_manual_callback(sys.stdin.readline())
            if manual:
                params = manual
                break
        time.sleep(0.1)
    else:
        raise TimeoutError("Timed out waiting for OAuth callback")

    if params.get("state") not in {expected_state, None}:
        raise RuntimeError("OAuth callback state did not match the login request")
    if "error" in params:
        raise RuntimeError(
            f"OAuth authorization failed: {params.get('error')} {params.get('error_description', '')}"
        )
    if "code" not in params:
        raise RuntimeError("OAuth callback did not contain an authorization code")
    return params


class OAuthManager:
    TOKEN_FILE = "tokens.json"
    CLIENT_FILE = "oauth_client.json"
    DISCOVERY_FILE = "oauth_discovery.json"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = StateStore(settings.state_dir)

    async def ensure_access_token(self) -> str:
        token = self.store.read_json(self.TOKEN_FILE)
        if not token:
            raise AuthRequiredError(
                "No upstream OAuth token. Run `make bootstrap`, or run "
                "`docker compose run --rm --publish 127.0.0.1:8765:8765 robinhood-mcp auth`."
            )
        access_token = token.get("access_token")
        if access_token and int(token.get("expires_at", 0)) > now_epoch() + 60:
            return str(access_token)
        if token.get("refresh_token"):
            refreshed = await self.refresh_token(str(token["refresh_token"]))
            return str(refreshed["access_token"])
        raise AuthRequiredError("Upstream OAuth token is expired and no refresh token is available")

    async def refresh_token_from_state(self) -> dict[str, Any]:
        token = self.store.read_json(self.TOKEN_FILE)
        if not token or not token.get("refresh_token"):
            raise AuthRequiredError("No refresh token is available")
        return await self.refresh_token(str(token["refresh_token"]))

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        discovery = await self.load_or_discover()
        client = await self.load_or_register_client(discovery)
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client.client_id,
        }
        if client.client_secret:
            data["client_secret"] = client.client_secret
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as http:
            response = await http.post(discovery.token_endpoint, data=data)
        if response.status_code >= 400:
            raise AuthRequiredError(f"Refresh token failed with HTTP {response.status_code}")
        token = response.json()
        self.save_token(token)
        return token

    async def login(self) -> None:
        discovery = await self.discover()
        client = await self.load_or_register_client(discovery)
        verifier, challenge = pkce_pair()
        state = secrets.token_urlsafe(32)
        scopes = discovery.scopes_supported
        query = {
            "response_type": "code",
            "client_id": client.client_id,
            "redirect_uri": self.settings.auth_redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "resource": discovery.resource,
        }
        if scopes:
            query["scope"] = " ".join(scopes)
        auth_url = f"{discovery.authorization_endpoint}?{urllib.parse.urlencode(query)}"
        print("Open this URL in your browser to authenticate Robinhood MCP:")
        print(auth_url)
        params = await asyncio.to_thread(
            wait_for_callback,
            bind_host=self.settings.auth_callback_bind_host,
            port=self.settings.auth_callback_port,
            expected_state=state,
        )
        token = await self.exchange_code(
            discovery=discovery,
            client=client,
            code=params["code"],
            verifier=verifier,
        )
        self.save_token(token)
        print("Robinhood MCP OAuth token saved.")

    async def exchange_code(
        self,
        *,
        discovery: OAuthDiscovery,
        client: OAuthClient,
        code: str,
        verifier: str,
    ) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.auth_redirect_uri,
            "code_verifier": verifier,
            "client_id": client.client_id,
            "resource": discovery.resource,
        }
        if client.client_secret:
            data["client_secret"] = client.client_secret
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as http:
            response = await http.post(discovery.token_endpoint, data=data)
        if response.status_code >= 400:
            raise RuntimeError(f"Token exchange failed with HTTP {response.status_code}: {response.text}")
        return response.json()

    async def load_or_discover(self) -> OAuthDiscovery:
        data = self.store.read_json(self.DISCOVERY_FILE)
        if data:
            return OAuthDiscovery(
                authorization_endpoint=str(data["authorization_endpoint"]),
                token_endpoint=str(data["token_endpoint"]),
                registration_endpoint=data.get("registration_endpoint"),
                issuer=data.get("issuer"),
                scopes_supported=list(data.get("scopes_supported", [])),
                resource=str(data["resource"]),
            )
        return await self.discover()

    async def discover(self) -> OAuthDiscovery:
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as http:
            probe = await http.post(
                self.settings.upstream_url,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": self.settings.mcp_protocol_version,
                    "Mcp-Method": "tools/list",
                },
                json={"jsonrpc": "2.0", "id": "auth-discovery", "method": "tools/list"},
            )
            challenge = parse_www_authenticate(probe.headers.get("www-authenticate"))
            resource_metadata_url = challenge.get("resource_metadata")
            resource_metadata: dict[str, Any] = {}
            if resource_metadata_url:
                resource_response = await http.get(resource_metadata_url)
                resource_response.raise_for_status()
                resource_metadata = resource_response.json()

            authorization_servers = resource_metadata.get("authorization_servers") or []
            if authorization_servers:
                auth_server = str(authorization_servers[0])
            else:
                parsed = urllib.parse.urlparse(self.settings.upstream_url)
                auth_server = f"{parsed.scheme}://{parsed.netloc}"

            metadata = await self.fetch_auth_server_metadata(http, auth_server)
            scopes = challenge.get("scope", "")
            scopes_supported = scopes.split() if scopes else list(metadata.get("scopes_supported", []))
            discovery = OAuthDiscovery(
                authorization_endpoint=str(metadata["authorization_endpoint"]),
                token_endpoint=str(metadata["token_endpoint"]),
                registration_endpoint=metadata.get("registration_endpoint"),
                issuer=metadata.get("issuer"),
                scopes_supported=scopes_supported,
                resource=self.settings.upstream_url,
            )
            self.store.write_json(
                self.DISCOVERY_FILE,
                {
                    "authorization_endpoint": discovery.authorization_endpoint,
                    "token_endpoint": discovery.token_endpoint,
                    "registration_endpoint": discovery.registration_endpoint,
                    "issuer": discovery.issuer,
                    "scopes_supported": discovery.scopes_supported,
                    "resource": discovery.resource,
                },
            )
            return discovery

    async def fetch_auth_server_metadata(
        self,
        http: httpx.AsyncClient,
        auth_server: str,
    ) -> dict[str, Any]:
        if "/.well-known/" in auth_server:
            candidates = [auth_server]
        else:
            parsed = urllib.parse.urlparse(auth_server)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            path = parsed.path.strip("/")
            oauth_path = f"/.well-known/oauth-authorization-server/{path}" if path else "/.well-known/oauth-authorization-server"
            oidc_path = f"/.well-known/openid-configuration/{path}" if path else "/.well-known/openid-configuration"
            base = auth_server.rstrip("/")
            candidates = [
                f"{origin}{oauth_path}",
                f"{origin}{oidc_path}",
                f"{base}/.well-known/oauth-authorization-server",
                f"{base}/.well-known/openid-configuration",
            ]
        last_error: Exception | None = None
        for url in candidates:
            try:
                response = await http.get(url)
                if response.status_code < 400:
                    data = response.json()
                    if "authorization_endpoint" in data and "token_endpoint" in data:
                        return data
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"Could not discover OAuth authorization server metadata: {last_error}")

    async def load_or_register_client(self, discovery: OAuthDiscovery) -> OAuthClient:
        if self.settings.oauth_client_id:
            return OAuthClient(
                client_id=self.settings.oauth_client_id,
                client_secret=self.settings.oauth_client_secret,
            )
        data = self.store.read_json(self.CLIENT_FILE)
        if data:
            return OAuthClient(
                client_id=str(data["client_id"]),
                client_secret=data.get("client_secret"),
            )
        if not discovery.registration_endpoint:
            raise RuntimeError(
                "OAuth dynamic client registration is unavailable. Set "
                "ROBINHOOD_OAUTH_CLIENT_ID and ROBINHOOD_OAUTH_CLIENT_SECRET if Robinhood "
                "requires a pre-registered client."
            )
        payload = {
            "client_name": "Robinhood MCP Bridge",
            "redirect_uris": [self.settings.auth_redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as http:
            response = await http.post(discovery.registration_endpoint, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(
                f"OAuth dynamic client registration failed with HTTP {response.status_code}: {response.text}"
            )
        registered = response.json()
        client = OAuthClient(
            client_id=str(registered["client_id"]),
            client_secret=registered.get("client_secret"),
        )
        self.store.write_json(
            self.CLIENT_FILE,
            {"client_id": client.client_id, "client_secret": client.client_secret},
        )
        return client

    def save_token(self, token: dict[str, Any]) -> None:
        token = dict(token)
        expires_in = int(token.get("expires_in", 3600))
        token["expires_at"] = now_epoch() + expires_in
        self.store.write_json(self.TOKEN_FILE, token)
