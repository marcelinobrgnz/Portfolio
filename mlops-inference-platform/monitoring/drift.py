"""Batch drift detection with Evidently AI vs reference dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

from src.config import AWS_DEFAULT_REGION, DATA_DIR, FEATURE_COLUMNS, REPORTS_DIR, S3_BUCKET
from src.data import load_raw_wine_data


def _load_current(data_path: Path | None) -> pd.DataFrame:
    if data_path and data_path.exists():
        if data_path.suffix == ".parquet":
            return pd.read_parquet(data_path)
        return pd.read_csv(data_path)
    # Simulate production drift check: use a random subsample as "current"
    df = load_raw_wine_data()
    return df.sample(frac=0.3, random_state=7).reset_index(drop=True)


def generate_drift_report(
    reference_path: Path | None = None,
    current_path: Path | None = None,
    output_dir: Path | None = None,
    upload_s3: bool = False,
) -> Path:
    ref_path = reference_path or (DATA_DIR / "reference.parquet")
    if not ref_path.exists():
        load_raw_wine_data()
        ref_path = DATA_DIR / "reference.parquet"

    reference = pd.read_parquet(ref_path)
    current = _load_current(current_path)

    column_mapping = ColumnMapping(
        numerical_features=FEATURE_COLUMNS,
        target=None,
    )

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current, column_mapping=column_mapping)

    out_dir = output_dir or REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    html_path = out_dir / f"drift_report_{timestamp}.html"
    json_path = out_dir / f"drift_report_{timestamp}.json"

    report.save_html(str(html_path))

    drift_result = report.as_dict()
    summary = {
        "timestamp": timestamp,
        "reference_rows": len(reference),
        "current_rows": len(current),
        "dataset_drift": drift_result.get("metrics", []),
    }
    json_path.write_text(json.dumps(summary, indent=2, default=str))

    if upload_s3:
        _upload_to_s3(html_path, json_path)

    print(f"Drift report saved to {html_path}")
    return html_path


def _upload_to_s3(html_path: Path, json_path: Path) -> None:
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 required for S3 upload") from exc

    s3 = boto3.client("s3", region_name=AWS_DEFAULT_REGION)
    prefix = "drift-reports"
    for path in (html_path, json_path):
        key = f"{prefix}/{path.name}"
        s3.upload_file(str(path), S3_BUCKET, key)
        print(f"Uploaded s3://{S3_BUCKET}/{key}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Evidently drift report")
    parser.add_argument("--reference", type=Path, default=None)
    parser.add_argument("--current", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--upload-s3", action="store_true")
    args = parser.parse_args()

    generate_drift_report(
        reference_path=args.reference,
        current_path=args.current,
        output_dir=args.output_dir,
        upload_s3=args.upload_s3,
    )


if __name__ == "__main__":
    main()
