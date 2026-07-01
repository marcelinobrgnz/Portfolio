#!/usr/bin/env python3
"""Download one month of NYC Yellow Taxi Parquet (~47 MB compressed, ~2.8M rows)."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

# TLC trip records — Jan 2023 yellow taxi
TAXI_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "taxi"


def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  target = OUT_DIR / "yellow_tripdata_2023-01.parquet"
  if target.exists():
    print(f"Already exists: {target} ({target.stat().st_size / 1e6:.1f} MB)")
    return
  print(f"Downloading {TAXI_URL} ...")
  urlretrieve(TAXI_URL, target)
  print(f"Wrote {target} ({target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
  main()
