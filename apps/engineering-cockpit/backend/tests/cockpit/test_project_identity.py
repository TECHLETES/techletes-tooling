from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_template_identity_is_replaced() -> None:
    assert 'name = "engineering-cockpit"' in (
        PROJECT_ROOT / "pyproject.toml"
    ).read_text()
    assert '"name": "engineering-cockpit-frontend"' in (
        PROJECT_ROOT / "frontend/package.json"
    ).read_text()
    assert '"name": "Techletes Engineering Cockpit"' in (
        PROJECT_ROOT / ".devcontainer/devcontainer.json"
    ).read_text()
