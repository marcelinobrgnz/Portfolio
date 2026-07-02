"""Step 1: Verify AWS CLI credentials and Bedrock access in eu-west-1."""
from __future__ import annotations

import json
import os
import sys

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config.env"))

REGION = os.getenv("AWS_REGION", "eu-west-1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
DOCS_BUCKET = os.getenv("DOCS_BUCKET")


def main() -> int:
    print(f"Region: {REGION}")
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    print("AWS identity:", json.dumps(identity, indent=2))

    bedrock = boto3.client("bedrock", region_name=REGION)
    models = bedrock.list_foundation_models()
    embed_ok = any(m["modelId"] == EMBEDDING_MODEL for m in models["modelSummaries"])
    print(f"Embedding model available ({EMBEDDING_MODEL}): {embed_ok}")

    runtime = boto3.client("bedrock-runtime", region_name=REGION)
    try:
        runtime.invoke_model(
            modelId=EMBEDDING_MODEL,
            body=json.dumps({"inputText": "connectivity test"}),
            contentType="application/json",
            accept="application/json",
        )
        print("Bedrock embedding invoke: OK")
    except ClientError as exc:
        print("Bedrock embedding invoke FAILED:", exc.response["Error"]["Message"])
        print("Enable model access: Bedrock console -> Model access -> amazon.titan-embed-text-v2")
        return 1

    s3 = boto3.client("s3", region_name=REGION)
    s3.head_bucket(Bucket=DOCS_BUCKET)
    print(f"Documents bucket exists: {DOCS_BUCKET}")

    print("\nStep 1 complete. Ready for Knowledge Base (S3 Vectors) in Step 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
