import inspect

from robinhood_mcp_bridge.auth import OAuthManager, parse_www_authenticate
from robinhood_mcp_bridge.upstream import UpstreamMCPClient


def test_parse_www_authenticate_bearer_params():
    parsed = parse_www_authenticate(
        'Bearer resource_metadata="https://example.com/.well-known/oauth-protected-resource", scope="read write"'
    )
    assert parsed["resource_metadata"] == "https://example.com/.well-known/oauth-protected-resource"
    assert parsed["scope"] == "read write"


def test_auth_required_guidance_uses_current_docker_auth_flow():
    source = inspect.getsource(OAuthManager.ensure_access_token)
    assert "--service-ports" not in source
    assert "make bootstrap" in source
    assert "--publish 127.0.0.1:8765:8765" in source
    assert "robinhood-mcp auth`" in source


def test_upstream_token_rejection_guidance_uses_primary_auth_commands():
    source = inspect.getsource(UpstreamMCPClient.jsonrpc)
    assert "Re-run `make bootstrap` or `rh-mcp auth`" in source
    assert "auth login" not in source
