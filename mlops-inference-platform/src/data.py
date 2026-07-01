"""Data loading utilities for the UCI Wine Quality dataset."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from src.config import DATA_DIR, FEATURE_COLUMNS, FEATURE_STORE_PATH, TARGET_COLUMN, WINE_TYPE_MAP

RED_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "wine-quality/winequality-red.csv"
)
WHITE_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "wine-quality/winequality-white.csv"
)


def _download_if_missing(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        urlretrieve(url, destination)
    return destination


def load_raw_wine_data(data_dir: Path | None = None) -> pd.DataFrame:
    """Download (if needed) and combine red + white wine quality CSVs."""
    base = data_dir or DATA_DIR
    red_path = _download_if_missing(RED_URL, base / "winequality-red.csv")
    white_path = _download_if_missing(WHITE_URL, base / "winequality-white.csv")

    red = pd.read_csv(red_path, sep=";")
    white = pd.read_csv(white_path, sep=";")
    red.columns = red.columns.str.strip().str.replace(" ", "_")
    white.columns = white.columns.str.strip().str.replace(" ", "_")
    red["wine_type"] = "red"
    white["wine_type"] = "white"

    combined = pd.concat([red, white], ignore_index=True)
    combined["wine_type"] = combined["wine_type"].map(WINE_TYPE_MAP)
    return combined


def load_feature_store(path: str | Path | None = None) -> pd.DataFrame:
  """Load engineered features from local or S3 Parquet (Project 2 output)."""
  store = Path(path) if path else Path(FEATURE_STORE_PATH) if FEATURE_STORE_PATH else None
  if not store:
    raise ValueError("FEATURE_STORE_PATH is not set")

  if str(store).startswith("s3://"):
    return pd.read_parquet(store)

  if store.is_dir():
    return pd.read_parquet(store)

  return pd.read_parquet(store)


def load_training_data(
    data_source: str = "auto",
    feature_store_path: str | Path | None = None,
) -> pd.DataFrame:
  """Load training data from CSV (default) or Spark feature store (Parquet)."""
  if data_source == "feature_store":
    return load_feature_store(feature_store_path)
  if data_source == "csv":
    return load_raw_wine_data()
  if FEATURE_STORE_PATH:
    return load_feature_store(feature_store_path)
  return load_raw_wine_data()


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return feature matrix X and target vector y."""
    missing = set(FEATURE_COLUMNS + [TARGET_COLUMN]) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")
    return df[FEATURE_COLUMNS].copy(), df[TARGET_COLUMN].copy()


def save_reference_dataset(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Persist reference data for drift monitoring."""
    out = path or (DATA_DIR / "reference.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return out
