from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dependency_set_stays_lean():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "uvicorn[standard]" not in pyproject
    assert "respx" not in pyproject
    assert "twine" not in pyproject
    assert '"httpx>=0.27.0"' in pyproject
    assert '"starlette>=0.37.0"' in pyproject
    assert '"uvicorn>=0.29.0"' in pyproject
