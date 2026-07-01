"""API endpoint tests."""

from fastapi.testclient import TestClient

from src.serve.main import app


def test_health_without_model():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert "model_loaded" in body


def test_predict_schema_and_shape(client, sample_instance):
    payload = {"instances": [sample_instance, sample_instance]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "predictions" in body
    assert len(body["predictions"]) == 2
    assert all(isinstance(p, int) for p in body["predictions"])
    assert body["model_version"] == "test-run"


def test_predict_rejects_empty_instances(client):
    response = client.post("/predict", json={"instances": []})
    assert response.status_code == 422


def test_predict_503_when_model_missing(sample_instance):
    from src.serve.main import store

    store.model = None
    store.version = None
    client = TestClient(app)
    response = client.post("/predict", json={"instances": [sample_instance]})
    assert response.status_code == 503
