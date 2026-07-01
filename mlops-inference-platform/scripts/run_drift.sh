#!/usr/bin/env bash
# Generate Evidently drift report (optionally upload to S3 eu-west-1).
set -euo pipefail

cd "$(dirname "$0")/.."

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-eu-west-1}"
export S3_BUCKET="${S3_BUCKET:-mlops-inference-platform-864981752170}"

UPLOAD_S3=""
if [[ "${1:-}" == "--upload-s3" ]]; then
  UPLOAD_S3="--upload-s3"
  shift
fi

echo "==> Running drift check (reference vs current)"
python -m monitoring.drift ${UPLOAD_S3} "$@"

echo "==> Reports written to reports/"
