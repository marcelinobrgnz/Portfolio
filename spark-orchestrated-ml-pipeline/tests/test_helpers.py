"""Unit tests for pure-Python transform helpers."""

from __future__ import annotations

import pytest

from spark_jobs.helpers import (
    build_s3_feature_path,
    is_wine_row_valid,
    normalize_wine_column,
    normalize_wine_columns,
    parse_s3_uri,
    validate_row_count,
)


def test_normalize_wine_columns():
  assert normalize_wine_columns(["fixed acidity", "pH"]) == ["fixed_acidity", "pH"]


def test_normalize_wine_column_ph():
  assert normalize_wine_column("pH") == "pH"
  assert normalize_wine_column(" ph ") == "pH"


def test_validate_row_count_ok():
  validate_row_count(6500, 6000)


def test_validate_row_count_fail():
  with pytest.raises(ValueError, match="below minimum"):
    validate_row_count(100, 6000)


def test_is_wine_row_valid():
  row = {
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
      "quality": 5,
  }
  assert is_wine_row_valid(row)
  row["quality"] = 99
  assert not is_wine_row_valid(row)


def test_s3_helpers():
  assert build_s3_feature_path("my-bucket", "wine") == "s3://my-bucket/features/wine"
  bucket, key = parse_s3_uri("s3://my-bucket/features/taxi/part=1")
  assert bucket == "my-bucket"
  assert key == "features/taxi/part=1"
