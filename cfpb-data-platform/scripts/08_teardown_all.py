"""Teardown Snowflake + S3 + Databricks UC objects after screenshots."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
OUT = ROOT / "docs" / "snapshots_private"
OUT.mkdir(parents=True, exist_ok=True)


def teardown_snowflake() -> str:
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        authenticator="snowflake",
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )
    cur = conn.cursor()
    lines = []
    for stmt in [
        "USE ROLE ACCOUNTADMIN",
        "DROP DATABASE IF EXISTS CFPB_DB",
        "DROP WAREHOUSE IF EXISTS CFPB_WH",
    ]:
        print(f"SF> {stmt}", flush=True)
        cur.execute(stmt)
        lines.append(stmt + " OK")
    cur.execute("SHOW DATABASES LIKE 'CFPB%'")
    dbs = cur.fetchall()
    cur.execute("SHOW WAREHOUSES LIKE 'CFPB%'")
    whs = cur.fetchall()
    lines.append(f"SHOW DATABASES LIKE CFPB% -> {dbs}")
    lines.append(f"SHOW WAREHOUSES LIKE CFPB% -> {whs}")
    conn.close()
    text = "\n".join(lines) + "\n"
    (OUT / "M_teardown_snowflake.txt").write_text(text, encoding="utf-8")
    return text


def teardown_s3() -> str:
    import boto3

    bucket = os.getenv("S3_BUCKET", "").strip()
    prefix = os.getenv("S3_PREFIX", "cfpb/parquet").rstrip("/") + "/"
    region = os.getenv("AWS_REGION", "eu-west-1")
    if not bucket:
        return "S3_BUCKET empty — skip"
    s3 = boto3.resource("s3", region_name=region)
    b = s3.Bucket(bucket)
    deleted = 0
    for obj in b.objects.filter(Prefix=prefix):
        obj.delete()
        deleted += 1
    # also remove leftover cfpb/
    for obj in b.objects.filter(Prefix="cfpb/"):
        obj.delete()
        deleted += 1
    text = f"S3 deleted_objects~={deleted} bucket={bucket} prefix={prefix}\n"
    (OUT / "M_teardown_s3.txt").write_text(text, encoding="utf-8")
    print(text, flush=True)
    return text


def teardown_databricks() -> str:
    host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
    token = os.getenv("DATABRICKS_TOKEN", "").strip()
    if not host or not token:
        return "Databricks env missing — skip"
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    lines = []

    # Start warehouse for DROP TABLE
    wh = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID", "2c32a5430bfe11ed")
    requests.post(f"{host}/api/2.0/sql/warehouses/{wh}/start", headers=h, timeout=60)
    import time

    for _ in range(30):
        st = requests.get(f"{host}/api/2.0/sql/warehouses/{wh}", headers=h, timeout=60).json()
        if st.get("state") == "RUNNING":
            break
        time.sleep(5)

    def run_sql(sql: str) -> dict:
        r = requests.post(
            f"{host}/api/2.0/sql/statements",
            headers=h,
            json={
                "warehouse_id": wh,
                "catalog": "workspace",
                "schema": "cfpb",
                "statement": sql,
                "wait_timeout": "50s",
            },
            timeout=180,
        )
        data = r.json()
        sid = data.get("statement_id")
        state = data.get("status", {}).get("state")
        t0 = time.time()
        while state in ("PENDING", "RUNNING") and time.time() - t0 < 300:
            time.sleep(3)
            data = requests.get(
                f"{host}/api/2.0/sql/statements/{sid}", headers=h, timeout=60
            ).json()
            state = data.get("status", {}).get("state")
        lines.append(f"SQL {sql[:80]}... -> {state}")
        return data

    for sql in [
        "DROP TABLE IF EXISTS workspace.cfpb.fct_complaints_by_product_month",
        "DROP TABLE IF EXISTS workspace.cfpb.complaints_delta",
    ]:
        run_sql(sql)

    # Best-effort volume delete (may fail if not empty — try API)
    r = requests.delete(
        f"{host}/api/2.1/unity-catalog/volumes/workspace.cfpb.complaints",
        headers=h,
        timeout=60,
    )
    lines.append(f"DROP VOLUME -> {r.status_code} {r.text[:200]}")
    r = requests.delete(
        f"{host}/api/2.1/unity-catalog/schemas/workspace.cfpb",
        headers=h,
        timeout=60,
        params={"force": "true"},
    )
    lines.append(f"DROP SCHEMA -> {r.status_code} {r.text[:200]}")

    # stop warehouse
    requests.post(f"{host}/api/2.0/sql/warehouses/{wh}/stop", headers=h, timeout=60)
    lines.append("warehouse stop requested")

    text = "\n".join(lines) + "\n"
    (OUT / "M_teardown_databricks.txt").write_text(text, encoding="utf-8")
    print(text, flush=True)
    return text


def main() -> None:
    sf = teardown_snowflake()
    s3 = teardown_s3()
    dbx = teardown_databricks()
    summary = f"SNOWFLAKE\n{sf}\nS3\n{s3}\nDATABRICKS\n{dbx}\n"
    (OUT / "M_teardown_all.txt").write_text(summary, encoding="utf-8")
    print("TEARDOWN_OK", flush=True)


if __name__ == "__main__":
    main()
