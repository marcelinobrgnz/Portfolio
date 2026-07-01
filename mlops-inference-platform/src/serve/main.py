"""FastAPI inference service for wine quality classification."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException

from src.config import MODEL_METADATA_PATH, MODEL_PATH
from src.schemas import HealthResponse, PredictRequest, PredictResponse


class ModelStore:
    def __init__(self) -> None:
        self.model = None
        self.version: str | None = None

    def load(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        self.model = joblib.load(MODEL_PATH)
        if MODEL_METADATA_PATH.exists():
            meta = json.loads(MODEL_METADATA_PATH.read_text())
            self.version = meta.get("run_id", "local")
        else:
            self.version = "local"

    @property
    def is_loaded(self) -> bool:
        return self.model is not None


store = ModelStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        store.load()
    except FileNotFoundError:
        # Allow health checks in CI before training; /predict will 503
        pass
    yield


app = FastAPI(
    title="Wine Quality MLOps API",
    description="XGBoost classifier served via FastAPI — train → track → serve → monitor",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if store.is_loaded else "degraded",
        model_loaded=store.is_loaded,
        model_version=store.version,
    )


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    if not store.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded. Run training first.")

    vectors = [row.to_feature_vector() for row in request.instances]
    X = np.array(vectors, dtype=np.float32)
    predictions = store.model.predict(X).astype(int).tolist()

    return PredictResponse(predictions=predictions, model_version=store.version or "unknown")


@app.get("/")
def root() -> dict:
    return {
        "service": "mlops-inference-platform",
        "endpoints": ["/health", "/predict", "/docs"],
    }
