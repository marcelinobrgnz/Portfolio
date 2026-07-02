"""SageMaker BYOC Flask server for wine model."""

from __future__ import annotations

import json
import os

import joblib
import numpy as np
from flask import Flask, request

FEATURE_COLUMNS = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density",
    "pH", "sulphates", "alcohol", "wine_type",
]

app = Flask(__name__)
model = joblib.load("/opt/ml/model/wine_quality_model.pkl")


@app.get("/ping")
def ping():
    return "ok", 200


@app.post("/invocations")
def invocations():
    payload = request.get_json(force=True)
    instances = payload.get("instances", payload)
    rows = [[float(row[c]) for c in FEATURE_COLUMNS] for row in instances]
    preds = model.predict(np.array(rows, dtype=np.float32)).astype(int).tolist()
    return json.dumps({"predictions": preds}), 200, {"Content-Type": "application/json"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
