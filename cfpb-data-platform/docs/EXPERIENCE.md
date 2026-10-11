# EXPERIENCE pack — CFPB Data Platform

Fill this **after** the pipeline runs. Use for interviews, LinkedIn, resume.

## One-liner

Built a free/trial **CFPB → Parquet → Snowflake → dbt → Airflow** pipeline with automated tests and a parallel **Databricks Delta** path; documented contracts and same-day teardown.

## Stack

- Ingest: Python, pandas, PyArrow Parquet (partitioned by year)
- Cloud landing: local + optional S3 (`eu-west-1`)
- Warehouse: Snowflake (RAW VARIANT → typed view)
- Transform: dbt (staging, marts, **incremental merge**)
- Quality: dbt tests + `data_quality/contracts.json` row-count gate
- Orchestration: Airflow DAG (fail on dbt / contract failure)
- Lakehouse: Databricks Free Edition, PySpark, Delta

## Metrics (fill)

| Metric | Value |
|--------|-------|
| Source mode | sample / full |
| Rows loaded | |
| Snowflake = local? | yes / no |
| dbt build | pass / fail |
| Tests passed | |
| Incremental model | yes |
| Airflow run | yes / skipped |
| Databricks delta match | yes / no |
| Cost | ~$0 trial + local Docker |
| Teardown completed | date |

## What broke / how fixed (interview gold)

1. …
2. …
3. …

## Decisions worth defending

- **VARIANT landing** for schema drift vs rigid DDL on day 1
- **Internal stage + PUT** to avoid IAM on trial day
- **dbt severity warn** on evolving CFPB product taxonomy
- **Fail-on-test** in Airflow = production DE signal
- **Same dataset, two engines** (Snowflake + Databricks) without duplicating business logic in ad-hoc SQL forever (dbt owns warehouse marts)

## Resume bullets (approved only when green)

```
• Built Parquet → Snowflake → dbt analytics pipeline on CFPB complaints with
  automated tests and Airflow orchestration (fail-on-red-tests).
• Implemented incremental dbt merge model and row-count contracts from local
  Parquet to Snowflake RAW.
• Prototyped parallel lakehouse path in Databricks (PySpark → Delta) with
  count reconciliation; tore down trial resources same day.
```

## LinkedIn post hook (later)

> A pipeline isn’t done when data lands. It’s done when tests fail the DAG.

## Domain note

CFPB = US consumer financial complaints — supports **fintech / banking analytics** language without claiming you worked at a bank.
