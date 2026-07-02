# SecureGuard RAG — Resume

**Project** · Enterprise RAG Chatbot · AWS Bedrock · eu-west-1

---

## Entry (copy under Projects or Experience)

**SecureGuard RAG** — Enterprise Gen AI Policy Assistant  
*AWS Bedrock · RAG · LLM · Vector Database · AI Guardrails · Python*

- Built end-to-end **RAG** pipeline on **AWS Bedrock**: S3 document store, **Titan** embeddings, **S3 Vectors** vector database, **Bedrock Knowledge Base**, **Mistral Large** LLM — **no model training**, API-only inference.
- Applied **AI guardrails** (content filters, denied topics, PII rules); unsafe prompts blocked; policy answers returned with S3 source citations.
- Delivered **Streamlit** chat UI (upload + re-index), **Lambda** + **API Gateway** REST API, and **RAGAS-style** eval suite — 100% pass on 7 golden tests.
- Chose **S3 Vectors** over OpenSearch Serverless and serverless API over App Runner to keep infra cost under $5.

---
Architected a Gen AI-powered RAG chatbot (LLM: Mistral Large) for enterprise HR, IT security, travel, and benefits Q&A, grounded in cited sources.
Chose a vector database (S3 Vectors) over OpenSearch Serverless for retrieval, avoiding the ~$350/month baseline cost; total build spend stayed under $5.
Configured AI guardrails (Bedrock Guardrails) for content filtering, PII handling, and denied-topic blocking; verified hacking-intent prompts blocked end-to-end.
Shipped a serverless REST API (Lambda + API Gateway) and a Streamlit chat UI with live upload and re-indexing.
Built a RAGAS-inspired evaluation suite — 100% pass rate, 86% citation rate, 2.4s average latency across 7 golden tests.
---

## Bullets (pick 2–3 if space is tight)

- End-to-end **RAG** on **AWS Bedrock** — S3, **vector database** (S3 Vectors), Knowledge Base, **LLM** generation; no fine-tuning.
- **AI guardrails** for toxicity, hacking topics, and PII; answers grounded in HR/IT policy docs with citations.
- **Gen AI** chat UI + serverless `/ask` API; document sync and automated quality checks (faithfulness, latency, guardrail compliance).

---

## Skills line (paste under project or Skills section)

`RAG` · `Gen AI` · `LLM` · `Vector Database` · `AI Guardrails` · `AWS Bedrock` · `Amazon S3` · `S3 Vectors` · `Knowledge Base` · `Lambda` · `API Gateway` · `Python` · `boto3` · `Streamlit` · `Semantic Search` · `Embeddings`

---

## One-line summary (for compact CVs)

Enterprise **RAG** chatbot on **AWS Bedrock** — **LLM**-powered policy Q&A with **vector database** retrieval, **AI guardrails**, Streamlit UI, and serverless API; no model training.
