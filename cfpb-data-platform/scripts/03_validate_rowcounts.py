"""Data contract: local Parquet row counts + optional Snowflake compare.

Peak DE: fail loudly if counts diverge (ingest vs warehouse).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / os.getenv("CFPB_DATA_DIR", "data")
PARQUET_ROOT = DATA / "parquet" / "complaints"
CONTRACT = ROOT / "data_quality" / "contracts.json"


def count_parquet(root: Path) -> int:
    files = list(root.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet under {root}")
    try:
        import pyarrow.dataset as ds

        dataset = ds.dataset(str(root), format="parquet", partitioning="hive")
        return int(dataset.count_rows())
    except Exception:
        import pandas as pd

        total = 0
        for f in files:
            total += len(pd.read_parquet(f))
        return total


def maybe_snowflake_count() -> int | None:
    account = os.getenv("SNOWFLAKE_ACCOUNT", "").strip()
    user = os.getenv("SNOWFLAKE_USER", "").strip()
    password = os.getenv("SNOWFLAKE_PASSWORD", "").strip()
    if not (account and user and password):
        print("Snowflake env not set - skipping warehouse compare")
        return None
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "CFPB_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "CFPB_DB"),
        schema=os.getenv("SNOWFLAKE_SCHEMA_RAW", "RAW"),
    )
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM CFPB_DB.RAW.COMPLAINTS_RAW")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def main() -> None:
    local = count_parquet(PARQUET_ROOT)
    print(f"local_parquet_rows={local:,}")

    contract = {
        "dataset": "cfpb_complaints",
        "mode": os.getenv("CFPB_MODE", "full"),
        "local_parquet_rows": local,
        "rules": [
            "local_parquet_rows must equal Snowflake COMPLAINTS_RAW after COPY",
            "complaint_id should be unique in typed view (check in Snowflake)",
            "dbt build must be green before claiming skills",
        ],
    }
    CONTRACT.parent.mkdir(parents=True, exist_ok=True)

    sf = maybe_snowflake_count()
    if sf is not None:
        contract["snowflake_raw_rows"] = sf
        print(f"snowflake_raw_rows={sf:,}")
        if sf != local:
            contract["status"] = "FAIL"
            CONTRACT.write_text(json.dumps(contract, indent=2), encoding="utf-8")
            print("FAIL: row count mismatch local vs Snowflake", file=sys.stderr)
            sys.exit(1)
        print("PASS: local == Snowflake")
        contract["status"] = "PASS"
    else:
        contract["status"] = "LOCAL_ONLY"
        print("PASS: local contract recorded (warehouse not compared yet)")

    CONTRACT.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    print(f"Wrote {CONTRACT}")


if __name__ == "__main__":
    main()
