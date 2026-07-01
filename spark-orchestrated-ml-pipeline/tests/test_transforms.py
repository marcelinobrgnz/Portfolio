"""Integration tests for PySpark transforms (local mode)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

pytest.importorskip("pyspark")

from spark_jobs.transform import create_spark, transform_wine  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "wine"


@pytest.fixture(scope="module")
def spark():
  if not shutil.which("java"):
    pytest.skip("Java runtime not available (required for local PySpark)")
  session = create_spark("pytest-wine-etl", "local[2]")
  yield session
  session.stop()


def test_transform_wine_local(tmp_path_factory, spark):
  out = tmp_path_factory.mktemp("wine_features")
  stats = transform_wine(spark, str(FIXTURES), str(out))

  assert stats["row_count"] == 6
  assert stats["partitions"] == 2
  assert (out / "_metrics.json").exists() or list(out.rglob("*.parquet"))

  metrics_path = out / "_metrics_manual.json"
  metrics_path.write_text(json.dumps(stats), encoding="utf-8")
  assert stats["dataset"] == "wine"
