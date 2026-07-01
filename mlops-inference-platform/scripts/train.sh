#!/usr/bin/env bash
# Train wine quality model and log to MLflow.
set -euo pipefail

cd "$(dirname "$0")/.."

export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-sqlite:///mlflow.db}"
export MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-wine-quality}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-eu-west-1}"

echo "==> Training with MLflow at ${MLFLOW_TRACKING_URI}"
python -m src.train "$@"

echo "==> Model saved to models/wine_quality_model.pkl"
