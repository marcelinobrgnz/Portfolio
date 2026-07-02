"""Remove Step 5 Lambda API to stop any hosting charges."""
from __future__ import annotations

import sys

import boto3
from botocore.exceptions import ClientError

REGION = "eu-west-1"
FUNCTION_NAME = "secureguard-rag-api"
API_NAME = "secureguard-rag-api"

lam = boto3.client("lambda", region_name=REGION)
apigw = boto3.client("apigatewayv2", region_name=REGION)


def main() -> int:
    print("Tearing down SecureGuard RAG API...")

    apis = apigw.get_apis().get("Items", [])
    for api in apis:
        if api.get("Name") == API_NAME:
            apigw.delete_api(ApiId=api["ApiId"])
            print(f"Deleted API: {api['ApiId']}")

    try:
        lam.delete_function(FunctionName=FUNCTION_NAME)
        print(f"Deleted Lambda: {FUNCTION_NAME}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

    print("Done. Lambda/API charges stopped. Bedrock KB/S3 still active (pennies).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
