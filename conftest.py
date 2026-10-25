import pytest


@pytest.fixture(autouse=True)
def database_path(tmp_path, monkeypatch):
    path = tmp_path / "undercover.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    return path
