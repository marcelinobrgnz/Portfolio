"""Airflow DAG: wine feature ETL → validate → trigger Project 1 MLflow retrain."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path("/opt/airflow")
SPARK_MASTER = os.getenv("SPARK_MASTER_URL", "spark://spark:7077")
S3_BUCKET = os.getenv("S3_BUCKET", "mlops-inference-platform-864981752170")
P1_ROOT = os.getenv("P1_PROJECT_ROOT", "/opt/mlops-inference-platform")
RAW_WINE = os.getenv("RAW_WINE_PATH", str(PROJECT_ROOT / "data/raw/wine"))
FEATURE_WINE_LOCAL = os.getenv("FEATURE_WINE_PATH", str(PROJECT_ROOT / "data/features/wine"))
MIN_WINE_ROWS = int(os.getenv("MIN_WINE_ROWS", "6000"))


def _ensure_wine_raw() -> None:
  raw = Path(RAW_WINE)
  raw.mkdir(parents=True, exist_ok=True)
  red = raw / "winequality-red.csv"
  white = raw / "winequality-white.csv"
  if red.exists() and white.exists():
    return
  subprocess.run(
      ["python", str(PROJECT_ROOT / "scripts/download_wine.py")],
      check=True,
      cwd=str(PROJECT_ROOT),
  )


def validate_wine_features(**context) -> dict:
  metrics_path = Path(FEATURE_WINE_LOCAL) / "_metrics.json"
  if not metrics_path.exists():
    raise FileNotFoundError(f"Missing Spark metrics: {metrics_path}")
  stats = json.loads(metrics_path.read_text(encoding="utf-8"))
  row_count = int(stats["row_count"])
  if row_count < MIN_WINE_ROWS:
    raise ValueError(f"Wine feature rows {row_count} < minimum {MIN_WINE_ROWS}")
  context["ti"].xcom_push(key="wine_row_count", value=row_count)
  return stats


def trigger_p1_training(**_context) -> dict:
  feature_path = os.getenv("P1_FEATURE_STORE_PATH", FEATURE_WINE_LOCAL)
  env = os.environ.copy()
  env["FEATURE_STORE_PATH"] = feature_path
  env["PYTHONPATH"] = P1_ROOT
  cmd = [
      "python",
      "-m",
      "src.train",
      "--data-source",
      "feature_store",
      "--feature-store-path",
      feature_path,
      "--no-register",
  ]
  result = subprocess.run(
      cmd,
      cwd=P1_ROOT,
      env=env,
      capture_output=True,
      text=True,
      check=True,
  )
  return {"stdout": result.stdout[-500:]}


default_args = {
    "owner": "mle",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="wine_feature_pipeline",
    description="Spark wine ETL → Parquet feature store → trigger P1 MLflow train",
    default_args=default_args,
    schedule="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["spark", "wine", "mlops", "project-1"],
) as dag:
  ingest_raw = PythonOperator(
      task_id="ingest_raw_wine",
      python_callable=_ensure_wine_raw,
  )

  spark_wine_etl = BashOperator(
      task_id="spark_transform_wine",
      bash_command=(
          "spark-submit "
          f"--master {SPARK_MASTER} "
          "--packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 "
          f"{PROJECT_ROOT}/spark_jobs/transform.py "
          f"--dataset wine --input {RAW_WINE} "
          f"--output {FEATURE_WINE_LOCAL} "
          f"--metrics-file {FEATURE_WINE_LOCAL}/_metrics.json"
      ),
  )

  validate_features = PythonOperator(
      task_id="validate_row_counts",
      python_callable=validate_wine_features,
  )

  sync_s3 = BashOperator(
      task_id="sync_features_to_s3",
      bash_command=(
          f"aws s3 sync {FEATURE_WINE_LOCAL} s3://{S3_BUCKET}/features/wine "
          f"--region eu-west-1"
      ),
  )

  retrain_p1 = PythonOperator(
      task_id="trigger_p1_retrain",
      python_callable=trigger_p1_training,
  )

  ingest_raw >> spark_wine_etl >> validate_features >> sync_s3 >> retrain_p1
