"""Delete ALL SecureGuard RAG AWS resources to stop billing."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config.env")

REGION = os.getenv("AWS_REGION", "eu-west-1")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "864981752170")

FUNCTION_NAME = "secureguard-rag-api"
API_NAME = "secureguard-rag-api"
LAMBDA_ROLE = "SecureGuardRAGLambdaRole"
KB_ROLE = "SecureGuardRAGBedrockKBRole"
KB_NAME = "secureguard-rag-kb"
DS_NAME = "secureguard-rag-s3-source"
GUARDRAIL_NAME = "secureguard-rag-guardrail"
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "secureguard-rag-docs-864981752170-eu-west-1")
VECTOR_BUCKET = os.getenv("VECTOR_BUCKET", "secureguard-rag-vectors")
VECTOR_INDEX = os.getenv("VECTOR_INDEX", "secureguard-kb-index")

KB_ID = os.getenv("KB_ID", "")
DATA_SOURCE_ID = os.getenv("DATA_SOURCE_ID", "")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID", "")

apigw = boto3.client("apigatewayv2", region_name=REGION)
lam = boto3.client("lambda", region_name=REGION)
logs = boto3.client("logs", region_name=REGION)
agent = boto3.client("bedrock-agent", region_name=REGION)
bedrock = boto3.client("bedrock", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
s3vectors = boto3.client("s3vectors", region_name=REGION)
iam = boto3.client("iam")


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def skip(msg: str) -> None:
    print(f"  --  {msg}")


def fail(msg: str, exc: ClientError) -> None:
    code = exc.response["Error"]["Code"]
    if code in {"ResourceNotFoundException", "NoSuchEntity", "NotFoundException"}:
        skip(f"{msg} (not found)")
    else:
        print(f"  ERR {msg}: {exc.response['Error']['Message']}", file=sys.stderr)
        raise


def delete_api() -> None:
    print("\n[1/8] API Gateway")
    for api in apigw.get_apis().get("Items", []):
        if api.get("Name") == API_NAME:
            apigw.delete_api(ApiId=api["ApiId"])
            ok(f"Deleted HTTP API {api['ApiId']}")


def delete_lambda() -> None:
    print("\n[2/8] Lambda")
    try:
        lam.delete_function(FunctionName=FUNCTION_NAME)
        ok(f"Deleted Lambda {FUNCTION_NAME}")
    except ClientError as exc:
        fail(f"Lambda {FUNCTION_NAME}", exc)

    log_group = f"/aws/lambda/{FUNCTION_NAME}"
    try:
        logs.delete_log_group(logGroupName=log_group)
        ok(f"Deleted log group {log_group}")
    except ClientError as exc:
        fail(f"Log group {log_group}", exc)


def find_kb_id() -> str | None:
    if KB_ID:
        return KB_ID
    token = None
    while True:
        kwargs = {}
        if token:
            kwargs["nextToken"] = token
        resp = agent.list_knowledge_bases(**kwargs)
        for kb in resp.get("knowledgeBaseSummaries", []):
            if kb["name"] == KB_NAME:
                return kb["knowledgeBaseId"]
        token = resp.get("nextToken")
        if not token:
            return None


def list_data_source_ids(kb_id: str) -> list[str]:
    ids: list[str] = []
    if DATA_SOURCE_ID:
        ids.append(DATA_SOURCE_ID)
    token = None
    while True:
        kwargs: dict = {"knowledgeBaseId": kb_id}
        if token:
            kwargs["nextToken"] = token
        resp = agent.list_data_sources(**kwargs)
        for ds in resp.get("dataSourceSummaries", []):
            if ds["dataSourceId"] not in ids:
                ids.append(ds["dataSourceId"])
        token = resp.get("nextToken")
        if not token:
            break
    return ids


def delete_knowledge_base() -> None:
    print("\n[3/8] Bedrock Knowledge Base")
    kb_id = find_kb_id()
    if not kb_id:
        skip("No knowledge base found")
        return

    for ds_id in list_data_source_ids(kb_id):
        try:
            agent.delete_data_source(knowledgeBaseId=kb_id, dataSourceId=ds_id)
            ok(f"Deleted data source {ds_id}")
        except ClientError as exc:
            fail(f"Data source {ds_id}", exc)

    time.sleep(3)

    try:
        agent.delete_knowledge_base(knowledgeBaseId=kb_id)
        ok(f"Deleted knowledge base {kb_id}")
    except ClientError as exc:
        fail(f"Knowledge base {kb_id}", exc)


def find_guardrail_id() -> str | None:
    if GUARDRAIL_ID:
        return GUARDRAIL_ID
    token = None
    while True:
        kwargs = {}
        if token:
            kwargs["nextToken"] = token
        resp = bedrock.list_guardrails(**kwargs)
        for item in resp.get("guardrails", []):
            if item["name"] == GUARDRAIL_NAME:
                return item["id"]
        token = resp.get("nextToken")
        if not token:
            return None


def delete_guardrail() -> None:
    print("\n[4/8] Bedrock Guardrail")
    guardrail_id = find_guardrail_id()
    if not guardrail_id:
        skip("No guardrail found")
        return
    try:
        bedrock.delete_guardrail(guardrailIdentifier=guardrail_id)
        ok(f"Deleted guardrail {guardrail_id}")
    except ClientError as exc:
        fail(f"Guardrail {guardrail_id}", exc)


def empty_s3_bucket(bucket: str) -> None:
    paginator = s3.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket):
        to_delete: list[dict] = []
        for version in page.get("Versions", []):
            to_delete.append({"Key": version["Key"], "VersionId": version["VersionId"]})
        for marker in page.get("DeleteMarkers", []):
            to_delete.append({"Key": marker["Key"], "VersionId": marker["VersionId"]})
        if to_delete:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": to_delete})

    paginator2 = s3.get_paginator("list_objects_v2")
    for page in paginator2.paginate(Bucket=bucket):
        contents = page.get("Contents", [])
        if contents:
            s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in contents]},
            )


def delete_s3_vectors() -> None:
    print("\n[5/8] S3 Vectors")
    try:
        indexes = s3vectors.list_indexes(vectorBucketName=VECTOR_BUCKET).get("indexes", [])
        for idx in indexes:
            name = idx.get("indexName", VECTOR_INDEX)
            s3vectors.delete_index(vectorBucketName=VECTOR_BUCKET, indexName=name)
            ok(f"Deleted vector index {name}")
    except ClientError as exc:
        fail(f"Vector index in {VECTOR_BUCKET}", exc)

    time.sleep(2)

    try:
        s3vectors.delete_vector_bucket(vectorBucketName=VECTOR_BUCKET)
        ok(f"Deleted vector bucket {VECTOR_BUCKET}")
    except ClientError as exc:
        fail(f"Vector bucket {VECTOR_BUCKET}", exc)


def delete_docs_bucket() -> None:
    print("\n[6/8] S3 documents bucket")
    try:
        empty_s3_bucket(DOCS_BUCKET)
        s3.delete_bucket(Bucket=DOCS_BUCKET)
        ok(f"Deleted bucket {DOCS_BUCKET}")
    except ClientError as exc:
        fail(f"Docs bucket {DOCS_BUCKET}", exc)


def delete_iam_role(role_name: str, policy_name: str) -> None:
    try:
        iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
    except ClientError:
        pass
    try:
        iam.delete_role(RoleName=role_name)
        ok(f"Deleted IAM role {role_name}")
    except ClientError as exc:
        fail(f"IAM role {role_name}", exc)


def delete_iam_roles() -> None:
    print("\n[7/8] IAM roles")
    delete_iam_role(LAMBDA_ROLE, "SecureGuardRAGLambdaPolicy")
    delete_iam_role(KB_ROLE, "SecureGuardRAGKBPolicy")


def verify_clean() -> None:
    print("\n[8/8] Verification")
    remaining: list[str] = []

    for api in apigw.get_apis().get("Items", []):
        if api.get("Name") == API_NAME:
            remaining.append(f"API Gateway: {api['ApiId']}")

    try:
        lam.get_function(FunctionName=FUNCTION_NAME)
        remaining.append(f"Lambda: {FUNCTION_NAME}")
    except ClientError:
        pass

    try:
        resp = agent.list_knowledge_bases()
        for kb in resp.get("knowledgeBaseSummaries", []):
            if kb["name"] == KB_NAME:
                remaining.append(f"Knowledge Base: {kb['knowledgeBaseId']}")
    except ClientError:
        pass

    try:
        resp = bedrock.list_guardrails()
        for g in resp.get("guardrails", []):
            if g["name"] == GUARDRAIL_NAME:
                remaining.append(f"Guardrail: {g['id']}")
    except ClientError:
        pass

    try:
        s3.head_bucket(Bucket=DOCS_BUCKET)
        remaining.append(f"S3 bucket: {DOCS_BUCKET}")
    except ClientError:
        pass

    try:
        buckets = s3vectors.list_vector_buckets().get("vectorBuckets", [])
        if any(b.get("vectorBucketName") == VECTOR_BUCKET for b in buckets):
            remaining.append(f"S3 Vectors bucket: {VECTOR_BUCKET}")
    except ClientError:
        pass

    for role in (LAMBDA_ROLE, KB_ROLE):
        try:
            iam.get_role(RoleName=role)
            remaining.append(f"IAM role: {role}")
        except ClientError:
            pass

    if remaining:
        print("  WARNING — resources still present:")
        for item in remaining:
            print(f"    - {item}")
    else:
        ok("All SecureGuard RAG AWS resources removed")


def main() -> int:
    print("=" * 60)
    print("SecureGuard RAG — FULL AWS TEARDOWN")
    print(f"Region: {REGION}  Account: {ACCOUNT_ID}")
    print("=" * 60)

    delete_api()
    delete_lambda()
    delete_knowledge_base()
    delete_guardrail()
    delete_s3_vectors()
    delete_docs_bucket()
    delete_iam_roles()
    verify_clean()

    print("\nTeardown complete. No ongoing SecureGuard RAG charges expected.")
    print("(Bedrock model access has no standing charge — pay-per-use only.)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ClientError as exc:
        print("\nTeardown failed:", exc.response["Error"]["Message"], file=sys.stderr)
        sys.exit(1)
