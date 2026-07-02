"""Upload documents to S3 and sync Bedrock Knowledge Base."""
from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config.env")

REGION = os.getenv("AWS_REGION", "eu-west-1")
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "")
DOCS_PREFIX = os.getenv("DOCS_PREFIX", "documents/")
KB_ID = os.getenv("KB_ID", "")
DATA_SOURCE_ID = os.getenv("DATA_SOURCE_ID", "")


def upload_file(local_path: Path, s3_key: str | None = None) -> str:
    """Upload a file to the docs bucket. Returns s3:// URI."""
    key = s3_key or f"{DOCS_PREFIX}uploads/{local_path.name}"
    s3 = boto3.client("s3", region_name=REGION)
    s3.upload_file(str(local_path), DOCS_BUCKET, key)
    return f"s3://{DOCS_BUCKET}/{key}"


def upload_bytes(content: bytes, filename: str) -> str:
    """Upload raw bytes (e.g. from Streamlit uploader)."""
    key = f"{DOCS_PREFIX}uploads/{filename}"
    s3 = boto3.client("s3", region_name=REGION)
    s3.put_object(Bucket=DOCS_BUCKET, Key=key, Body=content)
    return f"s3://{DOCS_BUCKET}/{key}"


def sync_local_folder(local_dir: Path) -> int:
    """Sync a local folder to S3 under documents/. Returns file count."""
    s3 = boto3.client("s3", region_name=REGION)
    count = 0
    for path in local_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(local_dir).as_posix()
        key = f"{DOCS_PREFIX}{rel}"
        s3.upload_file(str(path), DOCS_BUCKET, key)
        count += 1
    return count


def start_ingestion(wait: bool = True) -> dict:
    """Trigger KB ingestion job. Optionally wait until complete."""
    agent = boto3.client("bedrock-agent", region_name=REGION)
    resp = agent.start_ingestion_job(
        knowledgeBaseId=KB_ID,
        dataSourceId=DATA_SOURCE_ID,
        description="SecureGuard RAG document sync",
    )
    job = resp["ingestionJob"]
    job_id = job["ingestionJobId"]

    if not wait:
        return job

    while True:
        job = agent.get_ingestion_job(
            knowledgeBaseId=KB_ID,
            dataSourceId=DATA_SOURCE_ID,
            ingestionJobId=job_id,
        )["ingestionJob"]
        status = job["status"]
        if status in {"COMPLETE", "FAILED"}:
            if status == "FAILED":
                raise RuntimeError(f"Ingestion failed: {job.get('failureReasons', job)}")
            return job
        time.sleep(5)


def list_s3_documents() -> list[str]:
    """List document keys under the docs prefix."""
    s3 = boto3.client("s3", region_name=REGION)
    keys: list[str] = []
    token = None
    while True:
        kwargs = {"Bucket": DOCS_BUCKET, "Prefix": DOCS_PREFIX}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.append(obj["Key"])
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return keys
