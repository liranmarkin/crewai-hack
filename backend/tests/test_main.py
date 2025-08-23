from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Text-Aware Image Generation API"}


def test_endpoint() -> None:
    response = client.get("/test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Test endpoint working!"
    assert data["data"]["project"] == "Text-Aware Image Generation"
    assert data["data"]["backend"] == "FastAPI"
    assert data["data"]["ready"] is True