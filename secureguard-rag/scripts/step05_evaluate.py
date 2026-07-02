"""RAG evaluation metrics (RAGAS-inspired, lightweight, low cost)."""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import boto3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / "config.env")

REGION = os.getenv("AWS_REGION", "eu-west-1")
KB_ID = os.getenv("KB_ID", "")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "mistral.mistral-large-2402-v1:0")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "")
MODEL_ARN = f"arn:aws:bedrock:{REGION}::foundation-model/{LLM_MODEL_ID}"


@dataclass
class CaseResult:
    case_id: str
    question: str
    answer: str
    passed: bool
    has_citation: bool
    guardrail_action: str | None
    latency_ms: float
    notes: list[str] = field(default_factory=list)


def ask(client, question: str) -> tuple[dict, float]:
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
    start = time.perf_counter()
    resp = client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration=config,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    return resp, latency_ms


def has_citations(resp: dict) -> bool:
    return bool(resp.get("citations"))


def keyword_match(answer: str, keywords: list[str]) -> bool:
    text = answer.lower()
    return any(kw.lower() in text for kw in keywords)


def evaluate_case(resp: dict, case: dict, latency_ms: float) -> CaseResult:
    answer = resp.get("output", {}).get("text", "")
    guardrail = resp.get("guardrailAction")
    cited = has_citations(resp)
    notes: list[str] = []

    if case.get("expect_blocked"):
        passed = guardrail == "INTERVENED" or "blocked" in answer.lower()
        if not passed:
            notes.append("expected guardrail block")
    else:
        keywords = case.get("expected_keywords", [])
        kw_ok = keyword_match(answer, keywords) if keywords else True
        not_blocked = guardrail in (None, "NONE")
        passed = kw_ok and not_blocked
        if not kw_ok:
            notes.append(f"missing keywords: {keywords}")
        if not not_blocked:
            notes.append(f"unexpected guardrail: {guardrail}")

    return CaseResult(
        case_id=case["id"],
        question=case["question"],
        answer=answer,
        passed=passed,
        has_citation=cited,
        guardrail_action=guardrail,
        latency_ms=latency_ms,
        notes=notes,
    )


def main() -> int:
    cases_path = ROOT / "eval" / "test_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)

    results: list[CaseResult] = []
    print("Step 5a: RAG evaluation (RAGAS-inspired)")
    print(f"Running {len(cases)} test cases...\n")

    for case in cases:
        resp, latency = ask(client, case["question"])
        result = evaluate_case(resp, case, latency)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case_id} ({latency:.0f}ms)")
        if result.notes:
            print(f"       {', '.join(result.notes)}")

    n = len(results)
    pass_rate = sum(1 for r in results if r.passed) / n
    citation_rate = sum(1 for r in results if r.has_citation) / n
    avg_latency = sum(r.latency_ms for r in results) / n
    safe_cases = [r for r in results if r.case_id != "guardrail_block"]
    faithfulness = sum(1 for r in safe_cases if r.passed) / len(safe_cases)

    report = {
        "metrics": {
            "pass_rate": round(pass_rate, 3),
            "faithfulness_proxy": round(faithfulness, 3),
            "citation_rate": round(citation_rate, 3),
            "avg_latency_ms": round(avg_latency, 1),
        },
        "results": [
            {
                "id": r.case_id,
                "passed": r.passed,
                "has_citation": r.has_citation,
                "guardrail_action": r.guardrail_action,
                "latency_ms": round(r.latency_ms, 1),
                "answer_preview": r.answer[:200],
                "notes": r.notes,
            }
            for r in results
        ],
    }

    out_path = ROOT / "eval" / "last_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n--- Metrics ---")
    print(f"  Pass rate:          {pass_rate:.0%}")
    print(f"  Faithfulness proxy: {faithfulness:.0%}")
    print(f"  Citation rate:      {citation_rate:.0%}")
    print(f"  Avg latency:        {avg_latency:.0f} ms")
    print(f"\nReport saved: {out_path}")
    print(f"Est. Bedrock cost:  ~$0.05-0.20 for this run")
    return 0 if pass_rate >= 0.85 else 1


if __name__ == "__main__":
    sys.exit(main())
