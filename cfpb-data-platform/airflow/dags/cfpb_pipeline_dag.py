"""
Local Airflow (2.x) — CFPB peak-DE orchestration.

Pipeline:
  ingest_or_skip → validate_local → validate_snowflake → dbt_build → dq_gate

CFPB_SKIP_INGEST=1 (default in compose) skips multi-hour re-ingest when Parquet
already exists — still validates warehouse + runs dbt with fail-on-red-tests.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = os.environ.get(
    "CFPB_PROJECT_ROOT",
    "/opt/airflow/cfpb-data-platform",
)


def fail_if_contract_red(**_context):
    """Fail DAG if data_quality/contracts.json status is FAIL."""
    import json

    path = Path(PROJECT_ROOT) / "data_quality" / "contracts.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing contract file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    status = data.get("status")
    if status == "FAIL":
        raise AssertionError(f"Data quality contract FAIL: {data}")
    print(f"Contract status={status} OK")


def ingest_or_skip(**_context):
    """Re-ingest only when explicitly requested; otherwise require existing Parquet."""
    import json

    skip = os.getenv("CFPB_SKIP_INGEST", "1").lower() in ("1", "true", "yes")
    parquet = Path(PROJECT_ROOT) / "data" / "parquet" / "complaints"
    manifest = Path(PROJECT_ROOT) / "data" / "parquet" / "_manifest.json"
    files = list(parquet.rglob("*.parquet")) if parquet.exists() else []
    if skip and files:
        rows = None
        if manifest.exists():
            rows = json.loads(manifest.read_text(encoding="utf-8")).get("rows")
        print(f"SKIP ingest: {len(files)} parquet files rows={rows}")
        return
    if skip and not files:
        raise FileNotFoundError(
            "CFPB_SKIP_INGEST=1 but no parquet found — run scripts/02_ingest_to_parquet.py first"
        )
    import subprocess
    import sys

    subprocess.check_call(
        [sys.executable, "scripts/02_ingest_to_parquet.py"],
        cwd=PROJECT_ROOT,
    )


default_args = {
    "owner": "marcelino",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="cfpb_snowflake_dbt_pipeline",
    description="CFPB Parquet → Snowflake → dbt build (fail on test failure)",
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["cfpb", "snowflake", "dbt", "portfolio"],
) as dag:

    ingest = PythonOperator(
        task_id="ingest_parquet",
        python_callable=ingest_or_skip,
    )

    validate_local = BashOperator(
        task_id="validate_local_rowcounts",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python scripts/03_validate_rowcounts.py"
        ),
    )

    validate_warehouse = BashOperator(
        task_id="validate_snowflake_rowcounts",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python scripts/03_validate_rowcounts.py"
        ),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"set -a && . {PROJECT_ROOT}/.env && set +a && "
            f"cd {PROJECT_ROOT}/dbt_cfpb && "
            "dbt build --profiles-dir . --project-dir ."
        ),
    )

    dq_gate = PythonOperator(
        task_id="dq_contract_gate",
        python_callable=fail_if_contract_red,
    )

    alert_on_failure = BashOperator(
        task_id="alert_if_upstream_failed",
        trigger_rule="one_failed",
        bash_command=(
            'echo "ALERT: CFPB pipeline failed — dbt tests or contracts red. '
            'Check Airflow logs." && exit 1'
        ),
    )

    ingest >> validate_local >> validate_warehouse >> dbt_build >> dq_gate
    [ingest, validate_local, validate_warehouse, dbt_build, dq_gate] >> alert_on_failure
