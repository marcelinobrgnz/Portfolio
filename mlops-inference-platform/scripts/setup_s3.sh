#!/usr/bin/env bash
# One-time S3 bucket layout for MLflow artifacts and drift reports (eu-west-1).
set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-eu-west-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${S3_BUCKET:-mlops-inference-platform-${ACCOUNT_ID}}"

echo "==> Using bucket s3://${BUCKET} in ${REGION}"

if ! aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
  aws s3api create-bucket \
    --bucket "${BUCKET}" \
    --region "${REGION}" \
    --create-bucket-configuration LocationConstraint="${REGION}"
fi

aws s3api put-bucket-versioning \
  --bucket "${BUCKET}" \
  --versioning-configuration Status=Enabled

for prefix in mlflow-artifacts drift-reports models; do
  aws s3api put_object --bucket "${BUCKET}" --key "${prefix}/" || true
done

echo "==> S3 ready:"
echo "    MLFLOW_ARTIFACT_ROOT=s3://${BUCKET}/mlflow-artifacts"
echo "    DRIFT_REPORTS=s3://${BUCKET}/drift-reports/"
