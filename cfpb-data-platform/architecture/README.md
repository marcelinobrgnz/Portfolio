# Architecture diagram

Polished diagram: **`architecture.png`** (also `architecture.jpg`).

```
CFPB CSV
   → Python ingest
   → Parquet (local / optional S3)
   → Snowflake RAW (VARIANT + typed view)
   → dbt staging → marts (+ incremental)
   → Airflow DAG (fail on dbt test red)
   → Databricks Delta (parallel lakehouse path)
```

Title: **CFPB Data Platform — peak DE (portfolio)**  
Caption: **18.1M rows reconciled · trial resources · teardown same day**

Attach `architecture/architecture.png` to LinkedIn / Featured.
