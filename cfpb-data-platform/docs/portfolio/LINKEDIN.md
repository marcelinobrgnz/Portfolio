# CFPB Data Platform — LinkedIn

> Portfolio / trial project with documented same-day teardown — honest framing for recruiters.

---

## Where to add on LinkedIn

| Section | What to use below |
|---------|-------------------|
| **Projects** (recommended) | Title + dates + description + skills + link |
| **Featured** | Short blurb + link to repo; attach `architecture/architecture.png` or Airflow/dbt screenshot (crop secrets) |
| **Post** | “Short post” when you announce the repo |

**Dates:** Oct 2026 (or month you publish)  
**URL:** https://github.com/marcelinobrgnz/cfpb-data-platform

---

## Projects entry (copy-paste)

**CFPB Data Platform**  
Data Engineering · Analytics Engineering  
*Oct 2026*

**Snowflake** · **dbt** · **Apache Airflow** · **Databricks** · **Delta Lake** · Python · Parquet · AWS S3 · Data Quality

End-to-end analytics pipeline on **public CFPB consumer complaint data** (~18.1M rows): not “data landed” — **tests and contracts gate the DAG**.

- **Ingest:** Python → partitioned **Parquet** (year/month); row-count **contracts** vs local source
- **Warehouse:** **Snowflake** RAW (VARIANT landing) → typed views → **dbt** staging + marts (**incremental merge**)
- **Quality:** **20 dbt tests** (1 warn on evolving taxonomy); Airflow **fail-on-red** when dbt or contracts fail
- **Lakehouse:** Same dataset in **Databricks** (**PySpark** → **Delta**); **18,091,520** rows reconciled across local, Snowflake, and Delta
- **Ops:** Documented runbook, snapshots, **trial teardown** (cost-conscious)

**Skills:** Snowflake · dbt · Apache Airflow · Databricks · Delta Lake · ETL · Data Quality · Python · Parquet · AWS

---

## Experience-style bullets (if you use Projects description field)

Architected a **Parquet → Snowflake → dbt** pipeline on US **CFPB** complaints with automated tests and **Airflow** orchestration that fails the run when quality checks fail.

Implemented **incremental dbt** mart, **VARIANT** RAW landing for schema drift, and **row-count reconciliation** across local Parquet, Snowflake, and **Databricks Delta** (18.1M rows aligned).

Built **fail-on-test** orchestration and captured architecture, dbt docs, and teardown proof — portfolio project on free/trial tiers, not claimed as production bank tenure.

---

## Featured section (short blurb)

**CFPB Data Platform** — Public complaint data through **Snowflake**, **dbt** (tests + incremental model), **Airflow**, and **Databricks Delta**. ~18.1M rows with contract reconciliation. Portfolio build with documented teardown.

---

## Post — short (recommended)

**CFPB Data Platform — when tests fail, the DAG fails**

Built a full **analytics engineering** path on public **CFPB consumer complaint** data (~**18.1M** rows):

→ Python ingest → partitioned **Parquet** + row contracts  
→ **Snowflake** stage/COPY → **dbt** (4 models, **20 tests**, incremental mart)  
→ **Airflow** orchestration — **fail on red tests** (saw it fire on a bad run)  
→ **Databricks** **PySpark** → **Delta** — same row count reconciled end-to-end  

Portfolio / trial project with runbook, screenshots, and **same-day cloud teardown** — learning stack depth (**Snowflake · dbt · Airflow · Databricks**) on real volume, honestly labeled.

Repo: https://github.com/marcelinobrgnz/cfpb-data-platform

#DataEngineering #AnalyticsEngineering #dbt #Snowflake #Airflow #Databricks #DeltaLake #ETL #DataQuality #Python #AWS

---

## Post — hook-only (comment or first line)

> A pipeline isn’t done when data lands. It’s done when tests fail the DAG.

---

## Headline / About keyword line (optional)

Snowflake · dbt · Apache Airflow · Databricks · Delta Lake · ETL · Data Quality

---

## Resume bullet (one line)

Built Parquet → Snowflake → dbt pipeline on 18.1M CFPB complaints with 20 dbt tests and Airflow fail-on-red orchestration; parallel Databricks Delta path with row-count reconciliation (portfolio, documented teardown).

---

## Media to attach

1. `architecture/architecture.png` (safest — no account IDs)
2. Cropped **Airflow** DAG green grid (`docs/snapshots_private/H_airflow_dag_grid.png`)
3. **dbt build** success terminal (crop paths if needed)

Do **not** upload screenshots with tokens, account URLs, or passwords.

---

## Honesty (do not oversell on LinkedIn)

- Say **portfolio project**, **trial/free tiers**, or **hands-on build** — not “years at Snowflake in production.”
- CFPB domain supports **fintech / consumer financial analytics** language — not “I worked at a bank/PBM.”
