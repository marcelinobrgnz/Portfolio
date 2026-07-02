"""SecureGuard RAG chat UI with Bedrock Knowledge Base + Guardrails."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import boto3
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / "config.env")

from app.kb_sync import list_s3_documents, start_ingestion, upload_bytes

REGION = os.getenv("AWS_REGION", "eu-west-1")
KB_ID = os.getenv("KB_ID", "")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "mistral.mistral-large-2402-v1:0")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "")

MODEL_ARN = f"arn:aws:bedrock:{REGION}::foundation-model/{LLM_MODEL_ID}"


def get_client():
    return boto3.client("bedrock-agent-runtime", region_name=REGION)


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


def format_citations(response: dict) -> list[str]:
    cites: list[str] = []
    for citation in response.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            loc = ref.get("location", {})
            uri = loc.get("s3Location", {}).get("uri", "")
            if uri:
                cites.append(uri)
    return list(dict.fromkeys(cites))


def sidebar_docs() -> None:
    st.subheader("Documents")
    try:
        docs = list_s3_documents()
        st.caption(f"{len(docs)} files in S3 knowledge base")
        with st.expander("View files"):
            for key in docs:
                st.text(key.replace("documents/", ""))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not list docs: {exc}")

    uploaded = st.file_uploader(
        "Upload policy doc (.md, .txt, .pdf)",
        type=["md", "txt", "pdf"],
    )
    if uploaded and st.button("Upload & re-index", type="primary"):
        with st.spinner("Uploading and indexing..."):
            try:
                uri = upload_bytes(uploaded.getvalue(), uploaded.name)
                job = start_ingestion(wait=True)
                scanned = job.get("statistics", {}).get("numberOfDocumentsScanned", "?")
                st.success(f"Indexed. Scanned {scanned} docs. Uploaded to {uri}")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))


def main() -> None:
    st.set_page_config(page_title="SecureGuard RAG", page_icon="🛡️", layout="wide")
    st.title("SecureGuard RAG")
    st.caption("Enterprise Q&A · S3 Vectors · Bedrock Guardrails · Ireland (eu-west-1)")

    with st.sidebar:
        st.subheader("Config")
        st.write(f"**KB:** `{KB_ID}`")
        st.write(f"**Model:** `{LLM_MODEL_ID}`")
        if GUARDRAIL_ID:
            st.write(f"**Guardrail:** `{GUARDRAIL_ID}` v{GUARDRAIL_VERSION}")
        else:
            st.warning("Guardrail not configured.")

        st.divider()
        sidebar_docs()

        st.divider()
        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("**Try asking:**")
        st.markdown("- Parental leave weeks?")
        st.markdown("- MFA policy?")
        st.markdown("- Learning budget per year?")
        st.markdown("- International hotel limit?")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("guardrail"):
                st.warning(f"Guardrail: {msg['guardrail']}")
            if msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.code(src)

    prompt = st.chat_input("Ask about company policies...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                response = ask(prompt)
            except Exception as exc:  # noqa: BLE001
                st.error(f"AWS error: {exc}")
                return

            guardrail_action = response.get("guardrailAction")
            if guardrail_action and guardrail_action != "NONE":
                st.warning(f"Guardrail action: {guardrail_action}")

            answer = response.get("output", {}).get("text", "No answer returned.")
            sources = format_citations(response)
            st.markdown(answer)
            if sources:
                with st.expander("Sources"):
                    for src in sources:
                        st.code(src)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "guardrail": guardrail_action if guardrail_action != "NONE" else None,
        }
    )


if __name__ == "__main__":
    main()
