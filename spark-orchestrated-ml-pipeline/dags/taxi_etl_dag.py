"""Airflow DAG: NYC Yellow Taxi batch ETL for volume / Spark scale demo."""

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
RAW_TAXI = os.getenv("RAW_TAXI_PATH", str(PROJECT_ROOT / "data/raw/taxi"))
FEATURE_TAXI = os.getenv("FEATURE_TAXI_PATH", str(PROJECT_ROOT / "data/features/taxi"))
MIN_TAXI_ROWS = int(os.getenv("MIN_TAXI_ROWS", "100000"))
SPARK_PACKAGES = (
    "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262"
)


def _ensure_taxi_raw() -> None:
  raw = Path(RAW_TAXI)
  raw.mkdir(parents=True, exist_ok=True)
  if any(raw.glob("*.parquet")):
    return
  subprocess.run(
      ["python", str(PROJECT_ROOT / "scripts/download_nyc_taxi.py")],
      check=True,
      cwd=str(PROJECT_ROOT),
  )


def validate_taxi_features(**context) -> dict:
  metrics_path = Path(FEATURE_TAXI) / "_metrics.json"
  stats = json.loads(metrics_path.read_text(encoding="utf-8"))
  row_count = int(stats["row_count"])
  if row_count < MIN_TAXI_ROWS:
    raise ValueError(f"Taxi feature rows {row_count} < minimum {MIN_TAXI_ROWS}")
  context["ti"].xcom_push(key="taxi_row_count", value=row_count)
  return stats


default_args = {
    "owner": "mle",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="taxi_etl_pipeline",
    description="NYC Taxi PySpark ETL → partitioned Parquet on S3 (~2.8M trips/month)",
    default_args=default_args,
    schedule="@monthly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["spark", "taxi", "volume"],
) as dag:
  ingest = PythonOperator(
      task_id="ingest_raw_taxi",
      python_callable=_ensure_taxi_raw,
  )

  spark_etl = BashOperator(
      task_id="spark_transform_taxi",
      bash_command=(
          "spark-submit "
          f"--master {SPARK_MASTER} "
          f"--packages {SPARK_PACKAGES} "
          f"{PROJECT_ROOT}/spark_jobs/transform.py "
          f"--dataset taxi --input {RAW_TAXI} "
          f"--output {FEATURE_TAXI} "
          f"--metrics-file {FEATURE_TAXI}/_metrics.json"
      ),
  )

  validate = PythonOperator(
      task_id="validate_row_counts",
      python_callable=validate_taxi_features,
  )

  sync_s3 = BashOperator(
      task_id="sync_features_to_s3",
      bash_command=(
          f"aws s3 sync {FEATURE_TAXI} s3://{S3_BUCKET}/features/taxi "
          f"--region eu-west-1"
      ),
  )

  ingest >> spark_etl >> validate >> sync_s3
