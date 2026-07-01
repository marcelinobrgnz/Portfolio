#!/usr/bin/env python3
"""Download UCI wine quality CSVs into data/raw/wine/."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

WINE_ZIP = "https://archive.ics.uci.edu/static/public/186/wine+quality.zip"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "wine"


def main() -> None:
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  with urlopen(WINE_ZIP, timeout=120) as response:
    archive = zipfile.ZipFile(io.BytesIO(response.read()))
  for name in archive.namelist():
    if name.endswith(".csv"):
      target = OUT_DIR / Path(name).name
      target.write_bytes(archive.read(name))
      print(f"Wrote {target}")


if __name__ == "__main__":
  main()
