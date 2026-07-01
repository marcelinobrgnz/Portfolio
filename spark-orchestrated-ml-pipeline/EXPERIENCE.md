# Experience Guide — Project 2 (Spark + Airflow)

Use this document to rehearse the project as **real work experience** in interviews and on your resume.

---

## One-line summary

Built an Airflow-orchestrated PySpark batch pipeline that engineers wine quality features into a Parquet feature store on S3 and automatically triggers downstream XGBoost retraining in a companion MLflow project.

---

## Step-by-step: what you did and why

### Step 1 — Define the batch boundary
**What:** Split the ML lifecycle into **batch feature engineering** (P2) and **training/serving** (P1).  
**Why:** Mirrors real teams: data platform owns ETL; ML platform owns models.  
**Say in interview:** “I separated concerns so feature logic could scale on Spark without touching the serving API.”

### Step 2 — Raw data ingest
**What:** `scripts/download_wine.py` pulls UCI Wine Quality zip; `download_nyc_taxi.py` pulls TLC Jan 2023 Parquet.  
**Metrics:** 6,497 wine rows; **2,826,368** taxi trips in raw file.  
**Say:** “Wine feeds the production ML path; taxi proves Spark at millions of rows.”

### Step 3 — PySpark feature engineering
**What:** `spark_jobs/transform.py`  
- Wine: rename columns, outlier filters, derived ratios (`total_acidity`, `free_to_total_so2_ratio`), `partitionBy(wine_type)`  
- Taxi: `groupBy`/window stats on `PULocationID` × `pickup_hour`, fare per mile, trip duration  
**Say:** “I used window functions for zone-level rolling aggregates — the kind of thing that doesn’t fit in pandas at taxi scale.”

### Step 4 — Pure-Python test layer
**What:** `spark_jobs/helpers.py` + `tests/test_helpers.py` — column normalization, bounds validation, S3 path builders.  
**Why:** Fast CI without a cluster; business rules tested independently of Spark.  
**Say:** “Critical transforms are unit-tested in plain Python; Spark integration tests run in `local[*]`.”

### Step 5 — Airflow DAG with quality gates
**What:** `wine_feature_pipeline_dag.py`  
1. `ingest_raw_wine`  
2. `spark_transform_wine` (spark-submit to `spark://spark:7077`)  
3. `validate_row_counts` (fail if &lt; 6,000 rows)  
4. `sync_features_to_s3`  
5. `trigger_p1_retrain` → calls P1 `python -m src.train --data-source feature_store`  
**Say:** “The DAG doesn’t just run ETL — it validates row counts before training and syncs to S3 before downstream ML.”

### Step 6 — S3 feature store layout
**What:** `s3://mlops-inference-platform-864981752170/features/{wine|taxi}/`  
**Why:** S3-compatible layout works locally (`aws s3 sync`) or on EMR without code changes.  
**Say:** “Partitioned Parquet on S3 is the contract between data engineering and ML training.”

### Step 7 — Docker Compose stack
**What:** Airflow (webserver + scheduler + Postgres) + Bitnami Spark master/worker.  
**Ports:** Airflow `8081`, Spark UI `8080`.  
**Say:** “Full local stack at $0 — same DAG code could target MWAA or EMR with config changes.”

### Step 8 — CI
**What:** GitHub Actions runs `ruff` + pytest + `DagBag` import check.  
**Say:** “Broken DAGs fail CI before they hit the scheduler.”

---

## Numbers to memorize

| Metric | Value |
|--------|-------|
| Wine rows after ETL | ~6,400 |
| Taxi raw trips | 2.8M |
| Taxi raw file size | ~47 MB |
| Wine DAG tasks | 5 |
| Spark version | 3.5.4 |
| Airflow version | 2.10.4 |
| AWS region | eu-west-1 (Ireland) |
| Combined cloud cost | &lt;$2/mo S3 (under $10 total cap) |

---

## Interview Q&A

**Q: Why Airflow instead of cron?**  
A: Retries, dependency graph, observability, and a single place to gate training on data quality.

**Q: Why not Kafka?**  
A: Batch retrain weekly/monthly doesn’t need streaming; S3 + Airflow sensor/sync is the honest MLE story on a budget.

**Q: How does Project 1 get new data?**  
A: P1 `src.train` accepts `--data-source feature_store` and reads Parquet from `FEATURE_STORE_PATH` (local or S3).

**Q: What would you do in production?**  
A: MWAA or self-hosted Airflow on K8s, EMR Serverless for heavy taxi backfills, data contracts on feature schema, and Great Expectations alongside row-count checks.

---

## Resume bullets (pick 1–2)

1. Orchestrated PySpark feature ETL with Apache Airflow (5-task DAG), writing partitioned Parquet to S3 and triggering MLflow retraining on **6.4k** wine samples with row-count validation gates.

2. Built a **$0** local Spark + Airflow stack processing **2.8M** NYC taxi trips with window-aggregated zone features, pytest CI, and S3-compatible feature store layout in **eu-west-1**.

---

## Demo script (5 minutes)

1. Show Airflow DAG graph (`wine_feature_pipeline`).  
2. Show Spark UI during `spark_transform_wine`.  
3. Open `data/features/wine/_metrics.json` — row count.  
4. Run `trigger_p1_train.sh` → MLflow run in P1.  
5. Show S3 console: `features/wine/` prefixes.
