# Questions for you (answer these)

Reply with short answers so we can finish the live run today.

## Blocking

1. **Snowflake trial** — already created? (Y/N) If Y, which cloud/region?
2. **Databricks Free Edition** — already created? (Y/N)
3. **Docker Desktop** installed and running? (Y/N) — needed for Airflow
4. **AWS** — use **local-only** today (recommended) or upload to S3? (local / s3)
5. **CFPB size** — `sample` (~50k–200k rows) or `full` (large, slower)? Recommend **sample** for today.

## Non-blocking

6. OK to put repo under `d:\IIMA\Portfolio\cfpb-data-platform` and later push to `marcelinobrgnz/Portfolio`? (Y/N)
7. Prefer Snowsight UI PUT or SnowSQL CLI for file upload?
8. Any hard stop time tonight for teardown?

## Already decided (unless you override)

- Dataset: **CFPB**
- Pattern: S3/local Parquet → Snowflake → dbt → Airflow → Databricks
- Cost: free/trial + teardown same day
- Quality: contracts, tests, incremental model, fail-on-test DAG
