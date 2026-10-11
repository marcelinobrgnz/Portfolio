"""Ingest CFPB CSV -> partitioned Parquet (local). Optional S3 sync.

Peak DE for full dataset:
- chunked CSV read (never load multi-GB CSV into RAM)
- Hive-style partitions year=/month=
- Snappy Parquet, stable part naming
- ingest-time DQ gates + JSON manifest
- unbuffered progress logging
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Force line-buffered progress on Windows pipes / Tee-Object
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / os.getenv("CFPB_DATA_DIR", "data")
RAW_DIR = DATA / "raw"
OUT_DIR = DATA / "parquet" / "complaints"
CHUNKSIZE = int(os.getenv("CFPB_CHUNKSIZE", "200000"))


def pick_source() -> Path:
    sample = RAW_DIR / "complaints_sample.csv"
    full = RAW_DIR / "complaints.csv"
    mode = os.getenv("CFPB_MODE", "full").lower()
    if mode == "full":
        if not full.exists():
            raise FileNotFoundError(
                "CFPB_MODE=full but complaints.csv missing — run 01_download_cfpb.py"
            )
        return full
    if sample.exists():
        return sample
    if full.exists():
        return full
    raise FileNotFoundError("Run scripts/01_download_cfpb.py first")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Date received" in df.columns:
        dt = pd.to_datetime(df["Date received"], errors="coerce")
        df["_year"] = dt.dt.year.astype("Int64").astype(str).fillna("unknown")
        df["_month"] = dt.dt.month.apply(
            lambda x: f"{int(x):02d}" if pd.notna(x) else "00"
        )
    else:
        df["_year"] = "unknown"
        df["_month"] = "00"
    return df


def reset_out_dir() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_chunked(src: Path) -> tuple[int, dict]:
    """Stream CSV -> year/month Parquet parts. Returns (rows, dq_stats)."""
    reset_out_dir()
    part_counters: dict[tuple[str, str], int] = defaultdict(int)
    total = 0
    null_ids = 0
    years_seen: set[str] = set()
    t0 = time.time()

    reader = pd.read_csv(
        src,
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=str,
        encoding="utf-8",
        on_bad_lines="warn",
    )

    for i, chunk in enumerate(reader):
        chunk = normalize_columns(chunk)
        if "Complaint ID" in chunk.columns:
            ids = chunk["Complaint ID"]
            null_ids += int(
                ids.isna().sum() + (ids.astype(str).str.strip() == "").sum()
            )

        for (year, month), g in chunk.groupby(["_year", "_month"], dropna=False):
            years_seen.add(str(year))
            part_dir = OUT_DIR / f"year={year}" / f"month={month}"
            part_dir.mkdir(parents=True, exist_ok=True)
            n = part_counters[(str(year), str(month))]
            path = part_dir / f"part-{n:05d}.parquet"
            (
                g.drop(columns=["_year", "_month"], errors="ignore").to_parquet(
                    path, index=False, compression="snappy"
                )
            )
            part_counters[(str(year), str(month))] = n + 1
            total += len(g)

        elapsed = time.time() - t0
        rate = total / elapsed if elapsed else 0
        print(
            f"chunk={i} rows_so_far={total:,} rate={rate:,.0f}/s "
            f"parts={sum(part_counters.values())}",
            flush=True,
        )

    files = list(OUT_DIR.rglob("*.parquet"))
    dq = {
        "rows": total,
        "parquet_files": len(files),
        "null_or_blank_complaint_id": null_ids,
        "years": sorted(years_seen),
        "elapsed_sec": round(time.time() - t0, 1),
        "chunksize": CHUNKSIZE,
        "source": src.as_posix(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    if total <= 0:
        raise RuntimeError("DQ FAIL: zero rows written")
    if null_ids > total * 0.01:
        raise RuntimeError(
            f"DQ FAIL: null/blank Complaint ID rate too high ({null_ids}/{total})"
        )
    return total, dq


def optional_s3_sync(local_dir: Path) -> int:
    bucket = os.getenv("S3_BUCKET", "").strip()
    if not bucket:
        print("S3_BUCKET empty - skipping upload (local-only mode)", flush=True)
        return 0
    import boto3

    prefix = os.getenv("S3_PREFIX", "cfpb/parquet").rstrip("/")
    region = os.getenv("AWS_REGION", "eu-west-1")
    s3 = boto3.client("s3", region_name=region)
    n = 0
    for path in sorted(local_dir.rglob("*.parquet")):
        key = f"{prefix}/complaints/{path.relative_to(local_dir).as_posix()}"
        s3.upload_file(str(path), bucket, key)
        n += 1
        if n % 25 == 0:
            print(f"S3 uploaded {n} files...", flush=True)
    print(f"S3 sync complete files={n} s3://{bucket}/{prefix}/complaints/", flush=True)
    return n


def main() -> None:
    src = pick_source()
    mode = os.getenv("CFPB_MODE", "full")
    print(
        f"CFPB_MODE={mode} source={src} size_bytes={src.stat().st_size:,}",
        flush=True,
    )
    total, dq = write_chunked(src)
    meta = DATA / "parquet" / "_manifest.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "cfpb_complaints",
        "mode": mode,
        "rows": total,
        "out": OUT_DIR.as_posix(),
        "dq": dq,
    }
    meta.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest {meta}", flush=True)
    print(json.dumps(dq, indent=2), flush=True)
    s3n = optional_s3_sync(OUT_DIR)
    print(f"DONE parquet_root={OUT_DIR} rows={total:,} s3_files={s3n}", flush=True)


if __name__ == "__main__":
    main()
