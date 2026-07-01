"""Shared configuration for the wine quality MLOps platform."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "wine-quality")
REGISTERED_MODEL_NAME = "wine-quality-classifier"

MODEL_PATH = Path(os.getenv("MODEL_PATH", MODELS_DIR / "wine_quality_model.pkl"))
MODEL_METADATA_PATH = Path(
    os.getenv("MODEL_METADATA_PATH", MODELS_DIR / "model_metadata.json")
)

FEATURE_STORE_PATH = os.getenv("FEATURE_STORE_PATH", "")

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-1")
S3_BUCKET = os.getenv("S3_BUCKET", "mlops-inference-platform-864981752170")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

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

TARGET_COLUMN = "quality"

WINE_TYPE_MAP = {"red": 0, "white": 1}
