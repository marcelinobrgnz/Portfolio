# SNAPSHOTS checklist (filled 2026-10-01)

Store private images under `docs/snapshots_private/` (gitignored) or OneDrive.  
Do **not** commit secrets / account IDs in screenshots if avoidable (crop).

| ID | Capture | Path / link | Done |
|----|---------|-------------|------|
| A | Local ingest row count + contracts.json | `docs/snapshots_private/*_A_contracts.txt`, `data_quality/contracts.json` | [x] |
| B | Snowflake `COUNT(*)` on `COMPLAINTS_RAW` | `docs/snapshots_private/*_B_snowflake_raw_count.txt` (=18,091,520) | [x] |
| C | `LIST` stage files | `docs/snapshots_private/*_C_list_stage.txt` | [x] |
| D | `V_COMPLAINTS` sample rows | `docs/snapshots_private/*_D_v_complaints_sample.txt` | [x] |
| E | `dbt build` success | `docs/snapshots_private/*_E_dbt_build.txt` + Airflow `dbt_build` success | [x] |
| F | Mart tables in Snowflake | `docs/snapshots_private/*_F_mart_tables.txt` | [x] |
| G | dbt docs | `docs/dbt_site/` — serve: `python -m http.server 8766 --directory docs/dbt_site` | [x] |
| H | Airflow DAG green | `docs/snapshots_private/H_airflow_dag_grid.png`, `H_airflow_*.json` — DAG **success** | [x] |
| I | Airflow fail-on-test alert | earlier failed run triggered `alert_if_upstream_failed` | [x] |
| J | Databricks Parquet→Delta counts | `*_J_databricks_delta.txt`, `J_databricks_count_api.json` (=18,091,520) | [x] |
| K | Delta evidence card | `docs/snapshots_private/K_databricks_delta_evidence.html` + `.png` (live UI torn down; API-reconciled evidence) | [x] |
| L | Architecture diagram | `architecture/architecture.png` | [x] |
| M | Teardown proof | `docs/snapshots_private/M_teardown_*.txt` | [x] |

## Metrics recorded

- Local rows: **18,091,520**
- Snowflake rows: **18,091,520**
- dbt models built: **4** (1 view + 2 tables + 1 incremental)
- dbt tests passed: **20** (1 warn)
- Databricks delta rows: **18,091,520**
- Approx trial credits used: trial Snowflake MEDIUM load + XSMALL dbt; Databricks serverless SQL; S3 ~247MB (torn down)
- Airflow: WSL Docker engine + custom `cfpb-airflow:2.9.3`; stopped with `docker compose down -v`
- GitHub: https://github.com/marcelinobrgnz/Portfolio/tree/main/cfpb-data-platform
