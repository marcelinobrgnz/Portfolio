"""Step 4: Upload expanded docs to S3 and re-sync Knowledge Base."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.kb_sync import list_s3_documents, start_ingestion, sync_local_folder


def main() -> int:
    sample_dir = ROOT / "data" / "sample"
    print("Step 4: Sync documents to Knowledge Base")
    print(f"Uploading from: {sample_dir}")

    count = sync_local_folder(sample_dir)
    print(f"Uploaded {count} files to S3")

    keys = list_s3_documents()
    print(f"Total objects under documents/: {len(keys)}")
    for key in keys:
        print(f"  - {key}")

    print("Starting ingestion job...")
    job = start_ingestion(wait=True)
    stats = job.get("statistics", {})
    print(f"Ingestion COMPLETE")
    print(f"  Documents scanned: {stats.get('numberOfDocumentsScanned', '?')}")
    print(f"  New/modified indexed: {stats.get('numberOfNewDocumentsIndexed', '?')}")
    print("\nStep 4 complete. Refresh chat and try new questions:")
    print("  - What is the MFA policy?")
    print("  - What is the learning budget per year?")
    print("  - Hotel limit for international travel?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
