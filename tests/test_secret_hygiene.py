from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sensitive_local_state_is_ignored_and_not_packaged():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")

    assert ".rh-mcp-state/" in gitignore
    assert ".env" in gitignore
    assert "tokens.json" in gitignore
    assert "audit.jsonl" in gitignore
    assert ".rh-mcp-state" in dockerignore
    assert ".env" in dockerignore
    assert "tokens.json" in dockerignore
    assert "audit.jsonl" in dockerignore
    assert ".env.example" in manifest
    assert ".rh-mcp-state" not in manifest
    assert "tokens.json" not in manifest


def test_security_doc_names_common_local_secret_files():
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "tokens.json" in security
    assert "oauth_client.json" in security
    assert "oauth_discovery.json" in security
    assert "audit.jsonl" in security
