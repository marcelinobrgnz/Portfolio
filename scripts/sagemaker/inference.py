"""SageMaker sklearn container inference handler for wine_quality_model.pkl."""

from __future__ import annotations

import json
import os

import joblib
import numpy as np

FEATURE_COLUMNS = [
    "fixed_acidity",
    "volatile_acidity",
    "citric_acid",
    "residual_sugar",
    "chlorides",
    "free_sulfur_dioxide",
    "total_sulfur_dioxide",
    "density",
    "pH",
    "sulphates",
    "alcohol",
    "wine_type",
]


def model_fn(model_dir: str):
    return joblib.load(os.path.join(model_dir, "wine_quality_model.pkl"))


def input_fn(request_body, content_type):
    if content_type != "application/json":
        raise ValueError(f"Unsupported content type: {content_type}")
    payload = json.loads(request_body)
    instances = payload.get("instances", payload)
    rows = []
    for row in instances:
        rows.append([float(row[col]) for col in FEATURE_COLUMNS])
    return np.array(rows, dtype=np.float32)


def predict_fn(input_data, model):
    return model.predict(input_data).astype(int).tolist()


def output_fn(prediction, accept):
    body = json.dumps({"predictions": prediction})
    return body, "application/json"
