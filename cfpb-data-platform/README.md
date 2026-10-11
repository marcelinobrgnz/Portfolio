# CFPB Data Platform

**Marcelino Braganza** · Peak data-engineering portfolio project (trial / free-tier)

Part of the [Portfolio](../README.md) monorepo — Project 5.  
Canonical path: `https://github.com/marcelinobrgnz/Portfolio/tree/main/cfpb-data-platform`

Public **CFPB consumer complaint** data → **S3 Parquet** → **Snowflake** → **dbt** (tests + one incremental mart) → **Airflow** orchestration → **Databricks** Delta lakehouse notebook.

> **Honesty rule:** Claim this as a **hands-on portfolio / trial project**, not years of production Snowflake. Tear down cloud resources after screenshots (see `docs/TEARDOWN.md`).

## Architecture

```
CFPB CSV (public)
    → Python ingest → Parquet (local + optional S3)
    → Snowflake: stage + COPY INTO (RAW)
    → dbt: staging → marts (+ incremental) + tests
    → Airflow: ingest → load → dbt build (fail on red tests)
    → Databricks: same Parquet → Spark SQL / PySpark → Delta
```

See `architecture/README.md` for the diagram checklist (generate `architecture.png` when documenting).

## Cost posture (as low as possible)

| Component | Mode |
|-----------|------|
| Ingest / Parquet | **Local free** (`data/`) |
| S3 | Optional; empty bucket + delete after screenshots |
| Snowflake | **Trial credits only** — teardown same day |
| dbt | **Free** (`dbt-core` + `dbt-snowflake`) |
| Airflow | **Local Docker Compose** (free) |
| Databricks | **Free Edition** — delete cluster/tables after screenshots |

## Repo layout

```
cfpb-data-platform/
├── airflow/                 # DAG + docker-compose
├── aws/                     # Optional S3 sync scripts
├── snowflake/               # Database, stage, load SQL
├── dbt_cfpb/                # dbt project
├── databricks/              # Lakehouse notebook (.py + .ipynb notes)
├── scripts/                 # Ingest, validate, snapshot checklist helper
├── data_quality/            # Expectations / row-count contracts
├── architecture/
├── docs/                    # EXPERIENCE, RUNBOOK, SNAPSHOTS, TEARDOWN
├── data/                    # Local parquet (gitignored bulk)
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- Docker Desktop (Airflow)
- Snowflake trial account
- Databricks Free Edition workspace
- Optional: AWS CLI + account (`eu-west-1`)

## Quick start (order)

Default is **full** CFPB dump (`CFPB_MODE=full` in `.env`).

1. `python -m venv .venv && .venv\Scripts\activate` (Windows)
2. `pip install -r requirements.txt`
3. Copy `.env.example` → `.env` (Snowflake password, Databricks token, S3 bucket)
4. `python scripts/01_download_cfpb.py` — download + extract full CSV
5. `python scripts/02_ingest_to_parquet.py` — chunked Parquet `year=/month=` + optional S3
6. `python scripts/06_run_pipeline_after_ingest.py` — validate → Snowflake PUT/COPY → dbt build → Databricks
7. Optional: `docker compose -f airflow/docker-compose.yml up -d` → unpause DAG
8. Fill `docs/SNAPSHOTS.md` → run `docs/TEARDOWN.md` same day

Manual steps (instead of `06_`): `03_validate` → `04_snowflake_bootstrap` → `dbt build` → `05_databricks_bootstrap`.

## Resume bullets (only after green runs)

```
• Built S3/local Parquet → Snowflake → dbt pipeline with automated data-quality tests,
  orchestrated in Airflow (fail-on-test), using public CFPB consumer complaint data.
• Prototyped the same dataset in Databricks (PySpark + Delta) as a lakehouse path.
• Documented ingest contracts, row-count reconciliation, and same-day cloud teardown.
```

## Docs for experience later

| Doc | Purpose |
|-----|---------|
| `docs/EXPERIENCE.md` | Interview stories, metrics, what broke |
| `docs/RUNBOOK.md` | Exact commands |
| `docs/SNAPSHOTS.md` | What to capture |
| `docs/TEARDOWN.md` | Delete everything (cost control) |

## License

MIT · CFPB data is public domain (US government).
