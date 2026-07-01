"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from xgboost import XGBClassifier

from src.config import FEATURE_COLUMNS
from src.serve.main import app, store


@pytest.fixture()
def sample_instance() -> dict:
    return {
        "fixed_acidity": 7.4,
        "volatile_acidity": 0.7,
        "citric_acid": 0.0,
        "residual_sugar": 1.9,
        "chlorides": 0.076,
        "free_sulfur_dioxide": 11.0,
        "total_sulfur_dioxide": 34.0,
        "density": 0.9978,
        "pH": 3.51,
        "sulphates": 0.56,
        "alcohol": 9.4,
        "wine_type": 0,
    }


@pytest.fixture()
def trained_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Train a tiny model into a temp directory and wire the API to load it."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    model_path = model_dir / "wine_quality_model.pkl"
    meta_path = model_dir / "model_metadata.json"

    X = np.random.rand(60, len(FEATURE_COLUMNS)).astype(np.float32)
    y = np.random.randint(0, 3, size=60)
    model = XGBClassifier(
        n_estimators=10,
        max_depth=3,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
    )
    model.fit(X, y)
    joblib.dump(model, model_path)
    meta_path.write_text(json.dumps({"run_id": "test-run"}))

    monkeypatch.setattr("src.serve.main.MODEL_PATH", model_path)
    monkeypatch.setattr("src.serve.main.MODEL_METADATA_PATH", meta_path)

    store.model = None
    store.version = None
    store.load()

    yield model_path


@pytest.fixture()
def client(trained_model) -> TestClient:
    return TestClient(app)
