"""Step 2: Create Bedrock Knowledge Base with S3 Vectors (NOT OpenSearch)."""
from __future__ import annotations

import json
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
DOCS_BUCKET = os.getenv("DOCS_BUCKET")
DOCS_PREFIX = os.getenv("DOCS_PREFIX", "documents/")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

ROLE_NAME = "SecureGuardRAGBedrockKBRole"
VECTOR_BUCKET = "secureguard-rag-vectors"
VECTOR_INDEX = "secureguard-kb-index"
KB_NAME = "secureguard-rag-kb"
DS_NAME = "secureguard-rag-s3-source"
EMBED_DIM = 1024

iam = boto3.client("iam")
s3vectors = boto3.client("s3vectors", region_name=REGION)
agent = boto3.client("bedrock-agent", region_name=REGION)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_role() -> str:
    role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{ROLE_NAME}"
    trust = load_json(ROOT / "infra" / "iam" / "bedrock-kb-trust.json")
    policy = load_json(ROOT / "infra" / "iam" / "bedrock-kb-policy.json")

    try:
        iam.get_role(RoleName=ROLE_NAME)
        print(f"IAM role exists: {ROLE_NAME}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "NoSuchEntity":
            raise
        iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Bedrock Knowledge Base role for SecureGuard RAG",
        )
        print(f"Created IAM role: {ROLE_NAME}")
        time.sleep(10)

    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="SecureGuardRAGKBPolicy",
        PolicyDocument=json.dumps(policy),
    )
    return role_arn


def ensure_vector_store() -> tuple[str, str]:
    bucket_arn = f"arn:aws:s3vectors:{REGION}:{ACCOUNT_ID}:bucket/{VECTOR_BUCKET}"
    index_arn = f"{bucket_arn}/index/{VECTOR_INDEX}"

    buckets = s3vectors.list_vector_buckets().get("vectorBuckets", [])
    if not any(b.get("vectorBucketName") == VECTOR_BUCKET for b in buckets):
        s3vectors.create_vector_bucket(vectorBucketName=VECTOR_BUCKET)
        print(f"Created S3 vector bucket: {VECTOR_BUCKET}")
    else:
        print(f"S3 vector bucket exists: {VECTOR_BUCKET}")

    indexes = s3vectors.list_indexes(vectorBucketName=VECTOR_BUCKET).get("indexes", [])
    if not any(i.get("indexName") == VECTOR_INDEX for i in indexes):
        s3vectors.create_index(
            vectorBucketName=VECTOR_BUCKET,
            indexName=VECTOR_INDEX,
            dataType="float32",
            dimension=EMBED_DIM,
            distanceMetric="cosine",
        )
        print(f"Created vector index: {VECTOR_INDEX}")
    else:
        print(f"Vector index exists: {VECTOR_INDEX}")

    return bucket_arn, index_arn


def find_kb_id() -> str | None:
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


def create_kb(role_arn: str, bucket_arn: str, index_arn: str) -> str:
    existing = find_kb_id()
    if existing:
        print(f"Knowledge base exists: {existing}")
        return existing

    embedding_arn = f"arn:aws:bedrock:{REGION}::foundation-model/{EMBEDDING_MODEL}"
    resp = agent.create_knowledge_base(
        name=KB_NAME,
        description="SecureGuard enterprise RAG knowledge base (S3 Vectors)",
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": embedding_arn,
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {
                        "dimensions": EMBED_DIM,
                        "embeddingDataType": "FLOAT32",
                    }
                },
            },
        },
        storageConfiguration={
            "type": "S3_VECTORS",
            "s3VectorsConfiguration": {
                "vectorBucketArn": bucket_arn,
                "indexArn": index_arn,
            },
        },
    )
    kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
    print(f"Created knowledge base: {kb_id}")
    return kb_id


def find_data_source_id(kb_id: str) -> str | None:
    token = None
    while True:
        kwargs: dict = {"knowledgeBaseId": kb_id}
        if token:
            kwargs["nextToken"] = token
        resp = agent.list_data_sources(**kwargs)
        for ds in resp.get("dataSourceSummaries", []):
            if ds["name"] == DS_NAME:
                return ds["dataSourceId"]
        token = resp.get("nextToken")
        if not token:
            return None


def create_data_source(kb_id: str) -> str:
    existing = find_data_source_id(kb_id)
    if existing:
        print(f"Data source exists: {existing}")
        return existing

    resp = agent.create_data_source(
        knowledgeBaseId=kb_id,
        name=DS_NAME,
        description="Company policy documents from S3",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{DOCS_BUCKET}",
                "inclusionPrefixes": [DOCS_PREFIX],
            },
        },
        vectorIngestionConfiguration={
            "chunkingConfiguration": {
                "chunkingStrategy": "FIXED_SIZE",
                "fixedSizeChunkingConfiguration": {
                    "maxTokens": 300,
                    "overlapPercentage": 20,
                },
            },
        },
    )
    ds_id = resp["dataSource"]["dataSourceId"]
    print(f"Created data source: {ds_id}")
    return ds_id


def sync_data_source(kb_id: str, ds_id: str) -> str:
    resp = agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id,
        description="Initial sync for SecureGuard RAG",
    )
    job_id = resp["ingestionJob"]["ingestionJobId"]
    print(f"Started ingestion job: {job_id}")

    while True:
        job = agent.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            ingestionJobId=job_id,
        )["ingestionJob"]
        status = job["status"]
        print(f"  ingestion status: {status}")
        if status in {"COMPLETE", "FAILED"}:
            if status == "FAILED":
                print(json.dumps(job, indent=2, default=str))
                raise RuntimeError("Ingestion job failed")
            stats = job.get("statistics", {})
            print(f"  indexed documents: {stats.get('numberOfDocumentsScanned', '?')}")
            return job_id
        time.sleep(5)


def update_config(kb_id: str, ds_id: str, role_arn: str, bucket_arn: str, index_arn: str) -> None:
    lines = (ROOT / "config.env").read_text(encoding="utf-8").splitlines()
    updates = {
        "KB_ID": kb_id,
        "DATA_SOURCE_ID": ds_id,
        "KB_ROLE_ARN": role_arn,
        "VECTOR_BUCKET": VECTOR_BUCKET,
        "VECTOR_INDEX": VECTOR_INDEX,
        "VECTOR_BUCKET_ARN": bucket_arn,
        "VECTOR_INDEX_ARN": index_arn,
    }
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
    print("Step 2: Bedrock Knowledge Base + S3 Vectors")
    role_arn = ensure_role()
    bucket_arn, index_arn = ensure_vector_store()
    kb_id = create_kb(role_arn, bucket_arn, index_arn)
    ds_id = create_data_source(kb_id)
    sync_data_source(kb_id, ds_id)
    update_config(kb_id, ds_id, role_arn, bucket_arn, index_arn)
    print("\nStep 2 complete.")
    print(f"  KB_ID={kb_id}")
    print(f"  DATA_SOURCE_ID={ds_id}")
    print("Next: Step 3 = test retrieval + chat with guardrails")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ClientError as exc:
        print("AWS error:", exc.response["Error"]["Message"], file=sys.stderr)
        sys.exit(1)
