"""Upload Parquet to Unity Catalog Volume + build Delta via SQL Warehouse.

Free Edition compatible (DBFS FileStore often disabled).
Requires DATABRICKS_HOST + DATABRICKS_TOKEN.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
TOKEN = os.getenv("DATABRICKS_TOKEN", "").strip()
PARQUET = ROOT / "data" / "parquet" / "complaints"
VOLUME_ROOT = "/Volumes/workspace/cfpb/complaints"
WAREHOUSE_ID = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID", "2c32a5430bfe11ed")
CATALOG = "workspace"
SCHEMA = "cfpb"


def headers(json_mode: bool = True):
    h = {"Authorization": f"Bearer {TOKEN}"}
    if json_mode:
        h["Content-Type"] = "application/json"
    return h


def api(method: str, path: str, **kwargs):
    url = f"{HOST}{path}"
    r = requests.request(method, url, headers=headers(), timeout=180, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:900]}")
    return r.json() if r.text else {}


def ensure_uc() -> None:
    # schema + volume may already exist
    try:
        api(
            "POST",
            "/api/2.1/unity-catalog/schemas",
            json={"name": SCHEMA, "catalog_name": CATALOG, "comment": "CFPB portfolio"},
        )
    except RuntimeError as e:
        if "ALREADY_EXISTS" not in str(e) and "already exists" not in str(e).lower():
            # list to confirm
            schemas = api(
                "GET", f"/api/2.1/unity-catalog/schemas?catalog_name={CATALOG}"
            ).get("schemas", [])
            if not any(s.get("name") == SCHEMA for s in schemas):
                raise
    try:
        api(
            "POST",
            "/api/2.1/unity-catalog/volumes",
            json={
                "catalog_name": CATALOG,
                "schema_name": SCHEMA,
                "name": "complaints",
                "volume_type": "MANAGED",
                "comment": "CFPB parquet landing",
            },
        )
    except RuntimeError as e:
        if "ALREADY_EXISTS" not in str(e) and "already exists" not in str(e).lower():
            vols = api(
                "GET",
                f"/api/2.1/unity-catalog/volumes?catalog_name={CATALOG}&schema_name={SCHEMA}",
            ).get("volumes", [])
            if not any(v.get("name") == "complaints" for v in vols):
                raise
    print(f"UC ready: {CATALOG}.{SCHEMA}.complaints -> {VOLUME_ROOT}", flush=True)


def mkdir_p(path: str) -> None:
    # Create each path segment under Volumes
    parts = path.strip("/").split("/")
    cur = ""
    for p in parts:
        cur += "/" + p
        if cur in ("/Volumes", f"/Volumes/{CATALOG}", f"/Volumes/{CATALOG}/{SCHEMA}"):
            continue
        r = requests.request(
            "PUT",
            f"{HOST}/api/2.0/fs/directories{cur}",
            headers=headers(False),
            timeout=60,
        )
        if r.status_code not in (200, 204, 409):
            # 409 already exists is fine; some workspaces return 200
            if r.status_code == 400 and "already" in r.text.lower():
                continue
            if r.status_code >= 400 and r.status_code != 409:
                # directory may already exist
                if "RESOURCE_ALREADY_EXISTS" in r.text or "already exists" in r.text.lower():
                    continue
                # ignore if parent volume root
                pass


def upload_file(local: Path, volume_path: str) -> None:
    parent = "/".join(volume_path.rstrip("/").split("/")[:-1])
    mkdir_p(parent)
    data = local.read_bytes()
    url = f"{HOST}/api/2.0/fs/files{volume_path}"
    r = requests.put(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/octet-stream",
        },
        params={"overwrite": "true"},
        data=data,
        timeout=300,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"PUT {volume_path} -> {r.status_code}: {r.text[:500]}")


def upload_parquet() -> int:
    if not PARQUET.exists():
        raise FileNotFoundError(PARQUET)
    files = sorted(PARQUET.rglob("*.parquet"))
    max_files = int(os.getenv("DATABRICKS_MAX_FILES", "0") or "0")
    if max_files > 0:
        files = files[:max_files]
        print(f"DATABRICKS_MAX_FILES={max_files} (subset upload)", flush=True)
    n = 0
    for f in files:
        rel = f.relative_to(PARQUET).as_posix()
        dest = f"{VOLUME_ROOT}/{rel}"
        print(f"Volume put {rel} ({f.stat().st_size:,} bytes)", flush=True)
        upload_file(f, dest)
        n += 1
        if n % 25 == 0:
            print(f"uploaded {n}/{len(files)}", flush=True)
    print(f"Uploaded {n} parquet files to {VOLUME_ROOT}", flush=True)
    return n


def start_warehouse() -> None:
    api("POST", f"/api/2.0/sql/warehouses/{WAREHOUSE_ID}/start")
    t0 = time.time()
    while time.time() - t0 < 300:
        wh = api("GET", f"/api/2.0/sql/warehouses/{WAREHOUSE_ID}")
        state = wh.get("state")
        print(f"warehouse state={state}", flush=True)
        if state == "RUNNING":
            return
        time.sleep(10)
    raise TimeoutError("SQL warehouse did not start")


def run_sql(statement: str, timeout_s: int = 1200) -> dict:
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "catalog": CATALOG,
        "schema": SCHEMA,
        "statement": statement,
        "wait_timeout": "50s",
    }
    resp = api("POST", "/api/2.0/sql/statements", json=payload)
    sid = resp.get("statement_id")
    state = resp.get("status", {}).get("state")
    t0 = time.time()
    while state in ("PENDING", "RUNNING") and time.time() - t0 < timeout_s:
        time.sleep(5)
        resp = api("GET", f"/api/2.0/sql/statements/{sid}")
        state = resp.get("status", {}).get("state")
        print(f"sql state={state}", flush=True)
    if state != "SUCCEEDED":
        raise RuntimeError(json_dumps(resp))
    return resp


def json_dumps(obj) -> str:
    import json

    return json.dumps(obj, indent=2)[:2000]


def build_delta() -> None:
    print("Creating Delta table from volume parquet...", flush=True)
    # read_files + mergeSchema handles partition schema drift from hive parts
    run_sql(
        f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.complaints_delta
USING DELTA
TBLPROPERTIES (
  'delta.columnMapping.mode' = 'name',
  'delta.minReaderVersion' = '2',
  'delta.minWriterVersion' = '5'
)
AS
SELECT *
FROM read_files(
  '{VOLUME_ROOT}',
  format => 'parquet',
  mergeSchema => true,
  schemaEvolutionMode => 'rescue'
)
"""
    )
    cnt = run_sql(f"SELECT COUNT(*) AS n FROM {CATALOG}.{SCHEMA}.complaints_delta")
    data = cnt.get("result", {}).get("data_array")
    print(f"delta_count_raw={data}", flush=True)
    n = int(data[0][0]) if data else -1
    print(f"delta_rows={n}", flush=True)
    if n <= 0:
        raise RuntimeError(f"Delta table empty: {n}")
    if n != 18_091_520:
        print(f"WARN: expected 18091520 rows, got {n}", flush=True)

    # Discover product / date column names after merge
    cols = run_sql(f"SHOW COLUMNS IN {CATALOG}.{SCHEMA}.complaints_delta")
    print(f"delta_columns_sample={cols.get('result', {}).get('data_array', [])[:30]}", flush=True)

    run_sql(
        f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.fct_complaints_by_product_month
USING DELTA
AS
SELECT
  Product AS product,
  date_trunc('MONTH', try_to_timestamp(`Date received`)) AS month_start,
  COUNT(*) AS complaint_count
FROM {CATALOG}.{SCHEMA}.complaints_delta
WHERE Product IS NOT NULL AND `Date received` IS NOT NULL
GROUP BY 1, 2
"""
    )
    print("Delta mart created", flush=True)


def main() -> None:
    if not HOST or not TOKEN:
        print("ERROR: DATABRICKS_HOST / DATABRICKS_TOKEN required", file=sys.stderr)
        sys.exit(1)
    print(f"host={HOST}", flush=True)
    ensure_uc()
    n = upload_parquet()
    if n == 0:
        print("ERROR: no parquet uploaded", file=sys.stderr)
        sys.exit(1)
    start_warehouse()
    build_delta()
    print("DATABRICKS_OK", flush=True)


if __name__ == "__main__":
    main()
