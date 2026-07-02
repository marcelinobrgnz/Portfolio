"""Step 3a: Create and publish Bedrock Guardrail."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config.env")

REGION = os.getenv("AWS_REGION", "eu-west-1")
GUARDRAIL_NAME = "secureguard-rag-guardrail"

bedrock = boto3.client("bedrock", region_name=REGION)


def load_policy() -> dict:
    return json.loads((ROOT / "infra" / "guardrail" / "policy.json").read_text(encoding="utf-8"))


def find_guardrail_id() -> str | None:
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


def create_guardrail(policy: dict) -> str:
    existing = find_guardrail_id()
    if existing:
        print(f"Guardrail exists: {existing}")
        return existing

    resp = bedrock.create_guardrail(
        name=policy["name"],
        description=policy["description"],
        blockedInputMessaging=policy["blockedInputMessaging"],
        blockedOutputsMessaging=policy["blockedOutputsMessaging"],
        contentPolicyConfig=policy["contentPolicyConfig"],
        topicPolicyConfig=policy["topicPolicyConfig"],
        sensitiveInformationPolicyConfig=policy["sensitiveInformationPolicyConfig"],
    )
    guardrail_id = resp["guardrailId"]
    print(f"Created guardrail: {guardrail_id}")
    return guardrail_id


def publish_version(guardrail_id: str) -> str:
    versions = bedrock.list_guardrails(guardrailIdentifier=guardrail_id).get("guardrails", [])
    if versions and versions[0].get("version", "DRAFT") != "DRAFT":
        version = versions[0]["version"]
        print(f"Guardrail version exists: {version}")
        return version

    resp = bedrock.create_guardrail_version(guardrailIdentifier=guardrail_id)
    version = resp["version"]
    print(f"Published guardrail version: {version}")
    return version


def update_config(guardrail_id: str, version: str) -> None:
    lines = (ROOT / "config.env").read_text(encoding="utf-8").splitlines()
    updates = {
        "GUARDRAIL_ID": guardrail_id,
        "GUARDRAIL_VERSION": version,
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
    print("Step 3a: Create Bedrock Guardrail")
    policy = load_policy()
    guardrail_id = create_guardrail(policy)
    version = publish_version(guardrail_id)
    update_config(guardrail_id, version)
    print("\nStep 3a complete.")
    print(f"  GUARDRAIL_ID={guardrail_id}")
    print(f"  GUARDRAIL_VERSION={version}")
    print("Next: python -m streamlit run app/chat.py")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ClientError as exc:
        print("AWS error:", exc.response["Error"]["Message"], file=sys.stderr)
        sys.exit(1)
