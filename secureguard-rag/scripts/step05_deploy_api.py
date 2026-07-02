"""Step 5b: Deploy low-cost Lambda + HTTP API (typically under $5/month at demo scale)."""
from __future__ import annotations

import json
import os
import sys
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config.env")

REGION = os.getenv("AWS_REGION", "eu-west-1")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "864981752170")
FUNCTION_NAME = "secureguard-rag-api"
ROLE_NAME = "SecureGuardRAGLambdaRole"
API_NAME = "secureguard-rag-api"

iam = boto3.client("iam")
lam = boto3.client("lambda", region_name=REGION)
apigw = boto3.client("apigatewayv2", region_name=REGION)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_lambda_role() -> str:
    role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{ROLE_NAME}"
    try:
        iam.get_role(RoleName=ROLE_NAME)
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "NoSuchEntity":
            raise
        iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(load_json(ROOT / "infra" / "iam" / "lambda-rag-trust.json")),
            Description="Lambda role for SecureGuard RAG API",
        )
        time.sleep(10)
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="SecureGuardRAGLambdaPolicy",
        PolicyDocument=json.dumps(load_json(ROOT / "infra" / "iam" / "lambda-rag-policy.json")),
    )
    return role_arn


def build_zip() -> Path:
    zip_path = ROOT / "lambda" / "deployment.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(ROOT / "lambda" / "handler.py", "handler.py")
    return zip_path


def lambda_env() -> dict:
    # AWS_REGION is reserved and set automatically by Lambda.
    return {
        "Variables": {
            "KB_ID": os.getenv("KB_ID", ""),
            "LLM_MODEL_ID": os.getenv("LLM_MODEL_ID", ""),
            "GUARDRAIL_ID": os.getenv("GUARDRAIL_ID", ""),
            "GUARDRAIL_VERSION": os.getenv("GUARDRAIL_VERSION", ""),
        }
    }


def ensure_lambda(role_arn: str, zip_path: Path) -> str:
    with open(zip_path, "rb") as fh:
        zip_bytes = fh.read()

    try:
        lam.get_function(FunctionName=FUNCTION_NAME)
        lam.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_bytes)
        time.sleep(3)
        lam.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Environment=lambda_env(),
            Timeout=60,
            MemorySize=256,
        )
        print(f"Updated Lambda: {FUNCTION_NAME}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        lam.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": zip_bytes},
            Timeout=60,
            MemorySize=256,
            Environment=lambda_env(),
            Description="SecureGuard RAG API",
        )
        print(f"Created Lambda: {FUNCTION_NAME}")
        time.sleep(5)

    resp = lam.get_function(FunctionName=FUNCTION_NAME)
    return resp["Configuration"]["FunctionArn"]


def find_api_id() -> str | None:
    token = None
    while True:
        kwargs = {}
        if token:
            kwargs["NextToken"] = token
        resp = apigw.get_apis(**kwargs)
        for api in resp.get("Items", []):
            if api.get("Name") == API_NAME:
                return api["ApiId"]
        token = resp.get("NextToken")
        if not token:
            return None


def ensure_api(lambda_arn: str) -> str:
    api_id = find_api_id()
    if not api_id:
        resp = apigw.create_api(Name=API_NAME, ProtocolType="HTTP")
        api_id = resp["ApiId"]
        print(f"Created HTTP API: {api_id}")
    else:
        print(f"HTTP API exists: {api_id}")

    integrations = apigw.get_integrations(ApiId=api_id).get("Items", [])
    integration_id = integrations[0]["IntegrationId"] if integrations else None
    if not integration_id:
        resp = apigw.create_integration(
            ApiId=api_id,
            IntegrationType="AWS_PROXY",
            IntegrationUri=lambda_arn,
            PayloadFormatVersion="2.0",
        )
        integration_id = resp["IntegrationId"]

    routes = apigw.get_routes(ApiId=api_id).get("Items", [])
    route_keys = {r["RouteKey"] for r in routes}
    for route_key in ("POST /ask", "OPTIONS /ask"):
        if route_key not in route_keys:
            apigw.create_route(
                ApiId=api_id,
                RouteKey=route_key,
                Target=f"integrations/{integration_id}",
            )

    stages = apigw.get_stages(ApiId=api_id).get("Items", [])
    if not any(s.get("StageName") == "$default" for s in stages):
        apigw.create_stage(ApiId=api_id, StageName="$default", AutoDeploy=True)

    try:
        lam.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId="apigateway-invoke",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/*/*",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceConflictException":
            raise

    api = apigw.get_api(ApiId=api_id)
    return api["ApiEndpoint"]


def update_config(api_url: str) -> None:
    lines = (ROOT / "config.env").read_text(encoding="utf-8").splitlines()
    updates = {"API_URL": f"{api_url}/ask"}
    out: list[str] = []
    seen = set()
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line and not line.startswith("#") else None
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    (ROOT / "config.env").write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    print("Step 5b: Deploy Lambda + HTTP API (budget-friendly)")
    role_arn = ensure_lambda_role()
    zip_path = build_zip()
    lambda_arn = ensure_lambda(role_arn, zip_path)
    api_url = ensure_api(lambda_arn)
    update_config(api_url)

    print("\nStep 5b complete.")
    print(f"  API_URL={api_url}/ask")
    print("\nTest with:")
    print(f'  curl -X POST "{api_url}/ask" -H "Content-Type: application/json" -d "{{\\"question\\": \\"How many weeks of parental leave?\\"}}"')
    print("\nEstimated monthly cost at demo traffic: $0-2 (Lambda/API) + Bedrock per query")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ClientError as exc:
        print("AWS error:", exc.response["Error"]["Message"], file=sys.stderr)
        sys.exit(1)
