"""End-to-end orchestrator: validate -> Snowflake -> dbt -> Databricks.

Run after scripts/02_ingest_to_parquet.py finishes for CFPB_MODE=full.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n=== RUN: {' '.join(cmd)} ===", flush=True)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("CFPB_MODE", "full")
    p = subprocess.run(cmd, cwd=str(cwd or ROOT), env=env)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def main() -> None:
    py = sys.executable
    manifest = ROOT / "data" / "parquet" / "_manifest.json"
    if not manifest.exists():
        print("ERROR: parquet manifest missing — run 02_ingest_to_parquet.py first")
        raise SystemExit(1)

    run([py, "scripts/03_validate_rowcounts.py"])
    run([py, "scripts/04_snowflake_bootstrap.py"])
    run([py, "scripts/03_validate_rowcounts.py"])  # local == Snowflake gate

    dbt = ROOT / "dbt_cfpb"
    dbt_exe = ROOT / ".venv" / "Scripts" / "dbt.exe"
    dbt_cmd = [str(dbt_exe)] if dbt_exe.exists() else [py, "-m", "dbt.cli.main"]
    run(dbt_cmd + ["deps", "--profiles-dir", "."], cwd=dbt)
    run(dbt_cmd + ["build", "--profiles-dir", "."], cwd=dbt)

    run([py, "scripts/05_databricks_bootstrap.py"])
    print("\nPIPELINE_GREEN")


if __name__ == "__main__":
    main()
