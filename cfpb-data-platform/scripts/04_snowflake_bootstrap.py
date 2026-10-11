"""Bootstrap Snowflake: DDL + load from S3 (preferred) or local PUT fallback.

Peak DE path: Parquet on S3 -> external stage -> COPY INTO VARIANT RAW.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

import snowflake.connector


def connect():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        authenticator="snowflake",
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )


def run_sql_file(cur, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    while "/*" in text:
        a, b = text.find("/*"), text.find("*/")
        if a < 0 or b < 0:
            break
        text = text[:a] + text[b + 2 :]
    statements = []
    buf = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("--"):
            continue
        buf.append(line)
        if s.endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            buf = []
    if buf:
        stmt = "\n".join(buf).strip().rstrip(";").strip()
        if stmt:
            statements.append(stmt)
    for stmt in statements:
        preview = " ".join(stmt.split())[:120]
        print(f"SQL> {preview}...", flush=True)
        cur.execute(stmt)


def create_s3_stage(cur) -> str | None:
    bucket = os.getenv("S3_BUCKET", "").strip()
    prefix = os.getenv("S3_PREFIX", "cfpb/parquet").rstrip("/")
    key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    if not (bucket and key and secret):
        print("S3 credentials incomplete - will use internal PUT path", flush=True)
        return None

    url = f"s3://{bucket}/{prefix}/complaints/"
    # Escape single quotes in secret if any
    secret_esc = secret.replace("'", "\\'")
    key_esc = key.replace("'", "\\'")
    sql = f"""
CREATE OR REPLACE STAGE CFPB_DB.RAW.STG_COMPLAINTS_S3
  URL = '{url}'
  CREDENTIALS = (AWS_KEY_ID='{key_esc}' AWS_SECRET_KEY='{secret_esc}')
  FILE_FORMAT = CFPB_DB.RAW.FF_PARQUET
  COMMENT = 'External stage over portfolio S3 Parquet'
"""
    print(f"Creating S3 stage URL={url}", flush=True)
    cur.execute(sql)
    return "@CFPB_DB.RAW.STG_COMPLAINTS_S3"


def put_parquet(cur, parquet_root: Path) -> int:
    files = sorted(parquet_root.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet under {parquet_root}")
    n = 0
    for f in files:
        uri = f.resolve().as_posix()
        put_uri = f"file://{uri}"
        cmd = (
            f"PUT '{put_uri}' @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL "
            f"AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
        )
        if n % 20 == 0:
            print(f"PUT {n}/{len(files)} {f.name}", flush=True)
        cur.execute(cmd)
        n += 1
    return n


def copy_into(cur, stage_ref: str) -> None:
    cur.execute(
        """
CREATE OR REPLACE TABLE CFPB_DB.RAW.COMPLAINTS_RAW (
  SRC VARIANT,
  FILENAME STRING,
  FILE_ROW_NUMBER NUMBER,
  LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Landing: one VARIANT per Parquet row + lineage columns'
"""
    )
    sql = f"""
COPY INTO CFPB_DB.RAW.COMPLAINTS_RAW (SRC, FILENAME, FILE_ROW_NUMBER)
FROM (
  SELECT
    $1,
    METADATA$FILENAME,
    METADATA$FILE_ROW_NUMBER
  FROM {stage_ref}
)
FILE_FORMAT = (TYPE = PARQUET)
PATTERN = '.*[.]parquet'
ON_ERROR = 'ABORT_STATEMENT'
FORCE = TRUE
"""
    print(f"COPY INTO from {stage_ref} ...", flush=True)
    cur.execute(sql)
    print(f"COPY result rows={cur.rowcount}", flush=True)


def create_typed_view(cur) -> None:
    cur.execute(
        """
CREATE OR REPLACE VIEW CFPB_DB.RAW.V_COMPLAINTS AS
SELECT
  COALESCE(SRC:"Complaint ID", SRC:COMPLAINT_ID, SRC:"complaint_id")::STRING AS complaint_id,
  COALESCE(SRC:"Date received", SRC:DATE_RECEIVED, SRC:"date_received")::STRING AS date_received,
  COALESCE(SRC:"Product", SRC:PRODUCT, SRC:"product")::STRING AS product,
  COALESCE(SRC:"Sub-product", SRC:SUB_PRODUCT, SRC:"sub_product")::STRING AS sub_product,
  COALESCE(SRC:"Issue", SRC:ISSUE, SRC:"issue")::STRING AS issue,
  COALESCE(SRC:"Sub-issue", SRC:SUB_ISSUE, SRC:"sub_issue")::STRING AS sub_issue,
  COALESCE(
    SRC:"Consumer complaint narrative",
    SRC:CONSUMER_COMPLAINT_NARRATIVE,
    SRC:"consumer_complaint_narrative"
  )::STRING AS consumer_complaint_narrative,
  COALESCE(SRC:"Company public response", SRC:COMPANY_PUBLIC_RESPONSE)::STRING AS company_public_response,
  COALESCE(SRC:"Company", SRC:COMPANY, SRC:"company")::STRING AS company,
  COALESCE(SRC:"State", SRC:STATE, SRC:"state")::STRING AS state,
  COALESCE(SRC:"ZIP code", SRC:ZIP_CODE, SRC:"zip_code")::STRING AS zip_code,
  COALESCE(SRC:"Tags", SRC:TAGS)::STRING AS tags,
  COALESCE(SRC:"Consumer consent provided?", SRC:CONSUMER_CONSENT_PROVIDED)::STRING AS consumer_consent_provided,
  COALESCE(SRC:"Submitted via", SRC:SUBMITTED_VIA, SRC:"submitted_via")::STRING AS submitted_via,
  COALESCE(SRC:"Date sent to company", SRC:DATE_SENT_TO_COMPANY)::STRING AS date_sent_to_company,
  COALESCE(SRC:"Company response to consumer", SRC:COMPANY_RESPONSE_TO_CONSUMER)::STRING AS company_response_to_consumer,
  COALESCE(SRC:"Timely response?", SRC:TIMELY_RESPONSE, SRC:"timely_response")::STRING AS timely_response,
  COALESCE(SRC:"Consumer disputed?", SRC:CONSUMER_DISPUTED, SRC:"consumer_disputed")::STRING AS consumer_disputed,
  FILENAME,
  FILE_ROW_NUMBER,
  LOADED_AT
FROM CFPB_DB.RAW.COMPLAINTS_RAW
"""
    )


def main() -> None:
    parquet_root = ROOT / "data" / "parquet" / "complaints"
    if not parquet_root.exists():
        print("ERROR: run ingest first - no parquet", file=sys.stderr)
        sys.exit(1)

    conn = connect()
    cur = conn.cursor()
    try:
        for name in ["01_database.sql", "02_stage.sql"]:
            run_sql_file(cur, ROOT / "snowflake" / name)

        cur.execute("USE DATABASE CFPB_DB")
        cur.execute("USE SCHEMA RAW")
        cur.execute("USE WAREHOUSE CFPB_WH")

        print("Scaling warehouse to MEDIUM for full COPY...", flush=True)
        cur.execute("ALTER WAREHOUSE CFPB_WH SET WAREHOUSE_SIZE = 'MEDIUM'")

        stage_ref = create_s3_stage(cur)
        if stage_ref is None:
            try:
                cur.execute("REMOVE @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL")
            except Exception as e:
                print(f"REMOVE stage (ok if empty): {e}", flush=True)
            nfiles = put_parquet(cur, parquet_root)
            print(f"Uploaded files: {nfiles}", flush=True)
            stage_ref = "@CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL"

        copy_into(cur, stage_ref)
        create_typed_view(cur)

        cur.execute("SELECT COUNT(*) FROM CFPB_DB.RAW.COMPLAINTS_RAW")
        sf_count = cur.fetchone()[0]
        print(f"SNOWFLAKE_ROWS={sf_count}", flush=True)

        cur.execute(
            "SELECT COUNT(DISTINCT complaint_id) FROM CFPB_DB.RAW.V_COMPLAINTS"
        )
        distinct_ids = cur.fetchone()[0]
        print(f"DISTINCT_COMPLAINT_ID={distinct_ids}", flush=True)

        # Peak DE: if stage had stale duplicates, collapse to one row per complaint_id
        if distinct_ids and sf_count != distinct_ids:
            print(
                f"Deduping RAW {sf_count} -> {distinct_ids} by complaint_id...",
                flush=True,
            )
            cur.execute(
                """
CREATE OR REPLACE TABLE CFPB_DB.RAW.COMPLAINTS_RAW AS
SELECT SRC, FILENAME, FILE_ROW_NUMBER, LOADED_AT
FROM CFPB_DB.RAW.COMPLAINTS_RAW
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY COALESCE(SRC:"Complaint ID", SRC:COMPLAINT_ID, SRC:"complaint_id")::STRING
  ORDER BY LOADED_AT DESC, FILENAME
) = 1
"""
            )
            create_typed_view(cur)
            cur.execute("SELECT COUNT(*) FROM CFPB_DB.RAW.COMPLAINTS_RAW")
            sf_count = cur.fetchone()[0]
            print(f"SNOWFLAKE_ROWS_AFTER_DEDUP={sf_count}", flush=True)

        cur.execute("SELECT COUNT(*) FROM CFPB_DB.RAW.V_COMPLAINTS")
        print(f"VIEW_ROWS={cur.fetchone()[0]}", flush=True)

        cur.execute("SELECT SRC FROM CFPB_DB.RAW.COMPLAINTS_RAW LIMIT 1")
        sample = cur.fetchone()
        keys = None
        if sample and sample[0] is not None:
            src = sample[0]
            if isinstance(src, dict):
                keys = list(src.keys())
            else:
                # connector may return VARIANT as JSON string
                import json as _json

                try:
                    keys = list(_json.loads(src).keys()) if isinstance(src, str) else list(src.keys())
                except Exception:
                    keys = str(src)[:200]
        print(f"SAMPLE_SRC_KEYS={keys}", flush=True)

        print("Scaling warehouse back to XSMALL + suspend...", flush=True)
        cur.execute("ALTER WAREHOUSE CFPB_WH SET WAREHOUSE_SIZE = 'XSMALL'")
        try:
            cur.execute("ALTER WAREHOUSE CFPB_WH SUSPEND")
        except Exception as e:
            print(f"suspend note: {e}", flush=True)
    finally:
        conn.close()
    print("SNOWFLAKE_BOOTSTRAP_OK", flush=True)


if __name__ == "__main__":
    main()
