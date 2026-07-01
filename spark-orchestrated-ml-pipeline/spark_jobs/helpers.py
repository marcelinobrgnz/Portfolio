"""Pure-Python helpers for Spark transforms (unit-testable without a cluster)."""

from __future__ import annotations

import re
from typing import Iterable

WINE_COLUMN_RENAMES = {
    "fixed acidity": "fixed_acidity",
    "volatile acidity": "volatile_acidity",
    "citric acid": "citric_acid",
    "residual sugar": "residual_sugar",
    "free sulfur dioxide": "free_sulfur_dioxide",
    "total sulfur dioxide": "total_sulfur_dioxide",
}

WINE_REQUIRED_COLUMNS = [
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
    "quality",
]

WINE_TYPE_MAP = {"red": 0, "white": 1}

# Physicochemical bounds for outlier removal (UCI wine domain)
WINE_BOUNDS: dict[str, tuple[float, float]] = {
    "fixed_acidity": (3.0, 16.0),
    "volatile_acidity": (0.0, 2.0),
    "citric_acid": (0.0, 1.5),
    "residual_sugar": (0.0, 70.0),
    "chlorides": (0.0, 0.7),
    "free_sulfur_dioxide": (0.0, 300.0),
    "total_sulfur_dioxide": (0.0, 450.0),
    "density": (0.98, 1.01),
    "pH": (2.5, 4.5),
    "sulphates": (0.0, 2.0),
    "alcohol": (5.0, 17.0),
    "quality": (3.0, 9.0),
}


def normalize_wine_column(name: str) -> str:
  cleaned = name.strip().lower().replace(" ", "_")
  return "pH" if cleaned == "ph" else cleaned


def normalize_wine_columns(columns: Iterable[str]) -> list[str]:
  return [normalize_wine_column(c) for c in columns]


def validate_row_count(actual: int, minimum: int, label: str = "dataset") -> None:
  if actual < minimum:
    raise ValueError(f"{label} row count {actual} below minimum {minimum}")


def is_wine_row_valid(row: dict[str, float | int | str]) -> bool:
  for column, (low, high) in WINE_BOUNDS.items():
    value = row.get(column)
    if value is None:
      return False
    if not (low <= float(value) <= high):
      return False
  return True


def build_s3_feature_path(bucket: str, dataset: str, partition: str = "") -> str:
  base = f"s3://{bucket}/features/{dataset}"
  return f"{base}/{partition}".rstrip("/") if partition else base


def parse_s3_uri(uri: str) -> tuple[str, str]:
  match = re.match(r"^s3://([^/]+)/(.+)$", uri)
  if not match:
    raise ValueError(f"Invalid S3 URI: {uri}")
  return match.group(1), match.group(2)
