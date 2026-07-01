#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
P1_ROOT="${P1_PROJECT_ROOT:-$ROOT/../mlops-inference-platform}"
FEATURE_PATH="${1:-$ROOT/data/features/wine}"

export PYTHONPATH="$P1_ROOT"
export FEATURE_STORE_PATH="$FEATURE_PATH"

echo "==> Triggering Project 1 retrain from feature store: $FEATURE_PATH"
python -m src.train \
  --data-source feature_store \
  --feature-store-path "$FEATURE_PATH" \
  --no-register
