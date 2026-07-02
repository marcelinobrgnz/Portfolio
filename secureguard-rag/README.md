# SecureGuard RAG

Enterprise RAG chatbot on **AWS Bedrock** (Ireland / `eu-west-1`).

- **Vector store:** S3 Vectors (not OpenSearch Serverless)
- **No model training** — pre-trained APIs only
- **Region:** eu-west-1

## Project location

Part of the [Portfolio](https://github.com/marcelinobrgnz/Portfolio) monorepo:

```
Portfolio/secureguard-rag/
```

Copy `config.env.example` → `config.env` after provisioning AWS resources.

## Prerequisites

- AWS CLI configured (already working as `rascal-vertex`)
- Python 3.10+

## Steps (overview)

| Step | What |
|------|------|
| **1** | Verify AWS + create S3 docs bucket + sample document |
| **2** | Create Bedrock Knowledge Base with **S3 Vectors** |
| **3** | Bedrock Guardrails + Streamlit chat UI |
| **4** | More documents + upload & re-index pipeline |
| **5** | RAG evaluation + Lambda HTTP API (budget-friendly) |

---

## Step 4 — Expand knowledge base

```powershell
cd secureguard-rag
python scripts\step04_sync_documents.py
```

Adds IT security, travel/expense, and benefits docs — then re-indexes the KB.

Upload from the chat UI sidebar: **Upload policy doc** → **Upload & re-index**.

**New test questions:**
- `Is MFA mandatory?`
- `What is the annual learning budget?`
- `What is the international hotel limit per night?`

---

## Step 3 — Guardrails + chat

```powershell
cd secureguard-rag
python scripts\step03_create_guardrail.py
python scripts\step03_test_guardrail.py "How many weeks of parental leave do employees get?"
python -m streamlit run app/chat.py
```

Open **http://localhost:8501** in your browser.

---

## Step 1 — Run now

```powershell
cd secureguard-rag
python -m pip install -r requirements.txt
python scripts\step01_verify_aws.py
```

Upload sample docs:

```powershell
aws s3 sync data\sample s3://YOUR_DOCS_BUCKET/documents/sample/ --region eu-west-1
```

## Credentials

Uses your **existing AWS CLI profile** (`~/.aws/credentials`). No keys are stored in this repo.

## Step 2 — Run (already done if script succeeded)

```powershell
cd secureguard-rag
python scripts\step02_create_knowledge_base.py
```

Creates: IAM role, S3 Vectors bucket/index, Bedrock KB, data source, ingestion sync.

## Step 5 — Evaluation + HTTP API (under ~$5)

**5a — RAG evaluation** (~$0.05–0.20 per run, Bedrock only):

```powershell
cd secureguard-rag
python scripts\step05_evaluate.py
```

Writes `eval/last_report.json` with pass rate, citation rate, and latency.

**5b — Lambda + API Gateway** (~$0–2/month at demo traffic):

```powershell
python scripts\step05_deploy_api.py
```

Test the API (URL saved to `config.env` as `API_URL`):

```powershell
curl -X POST "%API_URL%" -H "Content-Type: application/json" -d "{\"question\": \"How many weeks of parental leave?\"}"
```

Teardown (stops Lambda/API charges):

```powershell
python scripts\step05_teardown_api.py
```

**Skipped for budget:** App Runner (~$5–25+/month minimum).

## Cost note

S3 Vectors = pay-per-use. **Do not** choose OpenSearch Serverless (~$350/mo minimum).
