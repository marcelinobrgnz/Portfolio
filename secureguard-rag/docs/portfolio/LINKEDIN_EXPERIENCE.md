# SecureGuard RAG — LinkedIn

---

## Experience / Project entry

**SecureGuard RAG**  
Enterprise Gen AI · Retrieval-Augmented Generation (RAG)  
*Jun 2026*

**AWS Bedrock** · **RAG** · **LLM** · **Vector Database** · **AI Guardrails** · Python · eu-west-1

Policy Q&A assistant for HR, IT security, travel, and benefits — answers pulled from company documents, not open-ended LLM output.

- **RAG** stack on **AWS Bedrock**: S3 docs → Titan embeddings → **S3 Vectors** (**vector database**) → Knowledge Base → Mistral Large **LLM** (no model training).
- **AI guardrails**: content filters, denied topics, PII handling; harmful prompts blocked at inference.
- Streamlit chat (upload + re-index), Lambda + API Gateway `/ask` endpoint, RAGAS-style eval — 7/7 golden tests passed.
- Cost-conscious design: S3 Vectors instead of OpenSearch Serverless; serverless API instead of always-on hosting.

**Skills:** RAG · Gen AI · LLM · Vector Database · AI Guardrails · AWS Bedrock · S3 · Lambda · Python

*Attach: `secureguard-rag-viewport.png`*

---
Architected a Gen AI-powered RAG chatbot (LLM: Mistral Large) for enterprise HR, IT security, travel, and benefits Q&A, grounded in cited sources.
Chose a vector database (S3 Vectors) over OpenSearch Serverless for retrieval — avoided the ~$350/month baseline cost, no cluster to manage.
Configured AI guardrails (Bedrock Guardrails) for content filtering, PII handling, and denied-topic blocking; verified hacking-intent prompts blocked end-to-end.
Shipped a serverless REST API (Lambda + API Gateway) and a Streamlit chat UI with live upload and re-indexing.
Built a RAGAS-inspired evaluation suite — 100% pass rate, 86% citation rate, 2.4s average latency across 7 golden tests.
Pivoted from Claude to Mistral Large (LLM) after a Bedrock access restriction — zero architecture rework.
---
## Featured section (short blurb)

**SecureGuard RAG** — Enterprise **RAG** chatbot on **AWS Bedrock**. Document-grounded Q&A using **S3 Vectors** as the **vector database**, **Mistral** **LLM**, and **Bedrock AI guardrails**. Includes Streamlit UI, serverless API, and eval suite. No model training.

---

## Post (optional — factual, no first person)

**SecureGuard RAG — enterprise RAG on AWS Bedrock**

Hands-on build: internal policy Q&A using **Retrieval-Augmented Generation (RAG)**, not standalone **LLM** chat.

Stack:
→ **AWS Bedrock** Knowledge Base + **S3 Vectors** (vector database)  
→ Titan embeddings · Mistral Large · **no model training**  
→ **AI guardrails** (toxicity, denied topics, PII)  
→ Streamlit UI · Lambda API · golden-test evaluation  

Example: parental leave policy → 26 weeks, with S3 source citations.  
Unsafe prompts (e.g. hacking) → blocked by guardrails.

Region: eu-west-1 (Ireland). Built and tested under $5 infra spend.

#AWS #Bedrock #RAG #GenAI #LLM #VectorDatabase #AIGuardrails #Python #Serverless #MachineLearning

---

## Headline keyword line (optional — append to About or headline)

RAG · Gen AI · LLM · Vector Database · AI Guardrails · AWS Bedrock
