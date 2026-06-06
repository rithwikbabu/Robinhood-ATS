from pathlib import Path

from robinhood_mcp_bridge import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_open_source_release_assets_exist():
    for path in [
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "RELEASE.md",
        "MANIFEST.in",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "docs/commands.md",
        "docs/quickstart.md",
        "examples/README.md",
    ]:
        assert (ROOT / path).exists(), path


def test_release_checklist_mentions_validation_and_secret_hygiene():
    release = (ROOT / "RELEASE.md").read_text(encoding="utf-8")
    assert "make check" in release
    assert "make bootstrap" in release
    assert "make stop" in release
    assert "make build-package" in release
    assert "tokens" in release
    assert "account numbers" in release
    assert ".rh-mcp-state" in release


def test_contributing_mentions_current_setup_flow():
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "make bootstrap" in contributing
    assert "make ready" not in contributing


def test_changelog_mentions_simplified_setup_surface():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for expected in [
        "make bootstrap",
        "build, authenticate, start the bridge, and check readiness",
        "make start",
        "make ready",
        "make stop",
        "MCP_HOST_PORT",
        "AUTH_HOST_PORT",
        "OAuth callback port `8765`",
        "`auth`",
        "`url`",
        "`ready`",
    ]:
        assert expected in changelog


def test_manifest_includes_open_source_package_assets():
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    for expected in [
        "include README.md",
        "include LICENSE",
        "include CHANGELOG.md",
        "include Dockerfile",
        "include docker-compose.yml",
        "recursive-include examples *.py *.json *.md",
        "recursive-include docs",
        "recursive-include tests",
        "recursive-include .github",
        "global-exclude __pycache__/*",
        "global-exclude *.py[cod]",
    ]:
        assert expected in manifest
    assert ".rh-mcp-state" not in manifest
    assert "tokens.json" not in manifest


def test_pyproject_uses_license_file_metadata():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = { file = "LICENSE" }' in pyproject


def test_pyproject_version_matches_package_version():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{__version__}"' in pyproject


def test_pyproject_exposes_open_source_project_urls():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'Homepage = "https://github.com/rithwikbabu/Robinhood-ATS"' in pyproject
    assert 'Documentation = "https://github.com/rithwikbabu/Robinhood-ATS#readme"' in pyproject
    assert 'Repository = "https://github.com/rithwikbabu/Robinhood-ATS"' in pyproject
    assert 'Issues = "https://github.com/rithwikbabu/Robinhood-ATS/issues"' in pyproject


def test_dockerfile_copies_license_for_local_install():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY pyproject.toml README.md LICENSE ./" in dockerfile


def test_dockerfile_exposes_only_steady_state_bridge_port():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "EXPOSE 8080" in dockerfile
    assert "EXPOSE 8080 8765" not in dockerfile


def test_compose_does_not_reserve_oauth_callback_port_for_bridge():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert '"127.0.0.1:${MCP_HOST_PORT:-8080}:8080"' in compose
    assert 'MCP_HOST_PORT: "${MCP_HOST_PORT:-8080}"' in compose
    assert '"127.0.0.1:8765:8765"' not in compose
