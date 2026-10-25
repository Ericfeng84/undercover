import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(autouse=True)
def database_path(tmp_path, monkeypatch):
    path = tmp_path / "undercover.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    return path


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
