"""Download CFPB Consumer Complaint Database CSV.

Source: Consumer Financial Protection Bureau (US public data).
Default: sample mode for same-day portfolio runs (fast, free).
Set CFPB_MODE=full for complete file (large).
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Official bulk CSV zip (CFPB). If URL moves, update RUNBOOK with current link.
CFPB_ZIP_URL = (
    "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / os.getenv("CFPB_DATA_DIR", "data")
RAW_DIR = DATA / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_zip(dest: Path) -> Path:
    zip_path = dest / "complaints.csv.zip"
    if zip_path.exists() and zip_path.stat().st_size > 1_000_000:
        print(f"Using cached {zip_path}")
        return zip_path

    print(f"Downloading {CFPB_ZIP_URL}")
    with requests.get(CFPB_ZIP_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(zip_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as bar:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
    return zip_path


def extract_csv(zip_path: Path) -> Path:
    csv_path = RAW_DIR / "complaints.csv"
    if csv_path.exists() and csv_path.stat().st_size > 1_000_000:
        print(f"Using cached {csv_path}")
        return csv_path

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
        if not members:
            raise RuntimeError(f"No CSV in {zip_path}")
        member = members[0]
        print(f"Extracting {member}")
        zf.extract(member, RAW_DIR)
        extracted = RAW_DIR / member
        if extracted != csv_path:
            extracted.replace(csv_path)
    return csv_path


def maybe_sample(csv_path: Path) -> Path:
    mode = os.getenv("CFPB_MODE", "sample").lower()
    sample_path = RAW_DIR / "complaints_sample.csv"
    if mode == "full":
        print("CFPB_MODE=full - using full CSV")
        return csv_path

    n = int(os.getenv("CFPB_SAMPLE_ROWS", "200000"))
    print(f"CFPB_MODE=sample - writing first {n:,} rows -> {sample_path}")
    # chunked read to avoid RAM blowups
    chunks = []
    rows = 0
    for chunk in pd.read_csv(csv_path, chunksize=50_000, low_memory=False, dtype=str):
        chunks.append(chunk)
        rows += len(chunk)
        if rows >= n:
            break
    df = pd.concat(chunks, ignore_index=True).head(n)
    df.to_csv(sample_path, index=False)
    print(f"Sample rows written: {len(df):,}")
    return sample_path


def main() -> None:
    zip_path = download_zip(RAW_DIR)
    csv_path = extract_csv(zip_path)
    out = maybe_sample(csv_path)
    print(f"DONE source_csv={out}")


if __name__ == "__main__":
    main()
