from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_data_empty():
    response = client.get("/api/v1/data")
    assert response.status_code == 200
    assert "data" in response.json()