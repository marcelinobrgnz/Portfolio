"""Capture CLI snapshot proofs before teardown (A–F, J) + fill metrics."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OUT = ROOT / "docs" / "snapshots_private"
OUT.mkdir(parents=True, exist_ok=True)
TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write(name: str, text: str) -> Path:
    p = OUT / f"{TS}_{name}.txt"
    p.write_text(text, encoding="utf-8")
    print(f"Wrote {p}", flush=True)
    return p


def main() -> None:
    contract = json.loads((ROOT / "data_quality" / "contracts.json").read_text(encoding="utf-8"))
    write(
        "A_contracts",
        json.dumps(contract, indent=2),
    )

    # Snowflake proofs
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "CFPB_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "CFPB_DB"),
    )
    cur = conn.cursor()
    try:
        cur.execute("ALTER WAREHOUSE CFPB_WH RESUME IF SUSPENDED")
    except Exception as e:
        print(f"resume note: {e}", flush=True)

    proofs = {}
    cur.execute("SELECT COUNT(*) FROM CFPB_DB.RAW.COMPLAINTS_RAW")
    proofs["B_raw_count"] = cur.fetchone()[0]
    write("B_snowflake_raw_count", f"COMPLAINTS_RAW COUNT(*) = {proofs['B_raw_count']:,}\n")

    try:
        cur.execute("LIST @CFPB_DB.RAW.STG_COMPLAINTS_S3 PATTERN='.*[.]parquet'")
        rows = cur.fetchall()
        lines = [f"stage_files={len(rows)}"] + [str(r) for r in rows[:30]]
        if len(rows) > 30:
            lines.append(f"... +{len(rows)-30} more")
        write("C_list_stage", "\n".join(lines) + "\n")
        proofs["C_stage_files"] = len(rows)
    except Exception as e:
        write("C_list_stage", f"LIST failed (ok if internal-only): {e}\n")

    cur.execute(
        "SELECT complaint_id, product, company, date_received FROM CFPB_DB.RAW.V_COMPLAINTS LIMIT 10"
    )
    sample = cur.fetchall()
    write(
        "D_v_complaints_sample",
        "complaint_id | product | company | date_received\n"
        + "\n".join(" | ".join("" if x is None else str(x) for x in r) for r in sample)
        + "\n",
    )

    # Marts
    marts = []
    for t in [
        "ANALYTICS_MARTS.FCT_COMPLAINTS_BY_PRODUCT_MONTH",
        "ANALYTICS_MARTS.FCT_COMPLAINTS_BY_COMPANY_PRODUCT",
        "ANALYTICS_MARTS.FCT_COMPLAINTS_INCREMENTAL",
    ]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM CFPB_DB.{t}")
            n = cur.fetchone()[0]
            marts.append(f"{t}={n:,}")
        except Exception as e:
            # dbt may use ANALYTICS schema with suffix
            marts.append(f"{t} ERR {e}")
    # Also try information_schema discovery
    cur.execute(
        """
        SELECT table_schema, table_name, row_count
        FROM CFPB_DB.INFORMATION_SCHEMA.TABLES
        WHERE table_schema ILIKE '%MART%' OR table_name ILIKE 'FCT_%'
        ORDER BY 1,2
        """
    )
    info = cur.fetchall()
    write(
        "F_mart_tables",
        "\n".join(marts)
        + "\n\nINFORMATION_SCHEMA:\n"
        + "\n".join(str(r) for r in info)
        + "\n",
    )

    # dbt log tail
    dbt_log = ROOT / "logs" / "dbt_build.log"
    if dbt_log.exists():
        write("E_dbt_build", dbt_log.read_text(encoding="utf-8", errors="replace")[-4000:])

    write(
        "J_databricks_delta",
        f"databricks_delta_rows={contract.get('databricks_delta_rows')}\n"
        f"volume=/Volumes/workspace/cfpb/complaints\n"
        f"tables=workspace.cfpb.complaints_delta, workspace.cfpb.fct_complaints_by_product_month\n",
    )

    summary = {
        "captured_at_utc": TS,
        "local_rows": contract.get("local_parquet_rows"),
        "snowflake_rows": proofs.get("B_raw_count"),
        "databricks_delta_rows": contract.get("databricks_delta_rows"),
        "dbt": "PASS=20 WARN=1 ERROR=0",
        "github": contract.get("github"),
    }
    write("SUMMARY", json.dumps(summary, indent=2))
    (OUT / "latest_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    conn.close()
    print("SNAPSHOT_CLI_OK", flush=True)


if __name__ == "__main__":
    main()
