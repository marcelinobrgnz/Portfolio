#!/usr/bin/env bash
set -euo pipefail

BUCKET="${S3_BUCKET:-mlops-inference-platform-864981752170}"
REGION="${AWS_DEFAULT_REGION:-eu-west-1}"

for prefix in raw/wine raw/taxi features/wine features/taxi pipeline-metrics; do
  aws s3api put-object --bucket "$BUCKET" --key "$prefix/" --region "$REGION" || true
done

echo "S3 prefixes ready on s3://$BUCKET/ (region $REGION)"
