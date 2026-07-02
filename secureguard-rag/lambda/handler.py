"""SecureGuard RAG HTTP API — Lambda handler (low-cost deploy)."""
import json
import os

import boto3

REGION = os.environ.get("AWS_REGION", "eu-west-1")
KB_ID = os.environ["KB_ID"]
LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID", "mistral.mistral-large-2402-v1:0")
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "")
MODEL_ARN = f"arn:aws:bedrock:{REGION}::foundation-model/{LLM_MODEL_ID}"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    return _client


def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }


def extract_citations(resp: dict) -> list[str]:
    uris: list[str] = []
    for citation in resp.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            uri = ref.get("location", {}).get("s3Location", {}).get("uri", "")
            if uri:
                uris.append(uri)
    return list(dict.fromkeys(uris))


def ask(question: str) -> dict:
    config: dict = {
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": KB_ID,
            "modelArn": MODEL_ARN,
        },
    }
    if GUARDRAIL_ID and GUARDRAIL_VERSION:
        config["knowledgeBaseConfiguration"]["generationConfiguration"] = {
            "guardrailConfiguration": {
                "guardrailId": GUARDRAIL_ID,
                "guardrailVersion": GUARDRAIL_VERSION,
            }
        }
    return get_client().retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration=config,
    )


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "POST")

    if method == "OPTIONS":
        return {"statusCode": 204, "headers": cors_headers(), "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    question = (body.get("question") or "").strip()
    if not question:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Missing 'question' field"}),
        }

    try:
        resp = ask(question)
    except Exception as exc:  # noqa: BLE001
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(exc)}),
        }

    payload = {
        "answer": resp.get("output", {}).get("text", ""),
        "sources": extract_citations(resp),
        "guardrail_action": resp.get("guardrailAction"),
    }
    return {
        "statusCode": 200,
        "headers": cors_headers(),
        "body": json.dumps(payload),
    }
