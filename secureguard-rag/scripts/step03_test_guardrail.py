"""Step 3b: Quick CLI test for RAG + guardrails."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config.env")

REGION = os.getenv("AWS_REGION", "eu-west-1")
KB_ID = os.getenv("KB_ID")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "mistral.mistral-large-2402-v1:0")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION")

QUESTION = sys.argv[1] if len(sys.argv) > 1 else "How many weeks of parental leave do employees get?"


def main() -> int:
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    config = {
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": KB_ID,
            "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{LLM_MODEL_ID}",
            "generationConfiguration": {
                "guardrailConfiguration": {
                    "guardrailId": GUARDRAIL_ID,
                    "guardrailVersion": GUARDRAIL_VERSION,
                }
            },
        },
    }
    resp = client.retrieve_and_generate(
        input={"text": QUESTION},
        retrieveAndGenerateConfiguration=config,
    )
    print("Question:", QUESTION)
    print("Answer:", resp.get("output", {}).get("text", ""))
    print("Guardrail action:", resp.get("guardrailAction"))
    print("Citations:", len(resp.get("citations", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
