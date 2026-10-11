# RUNBOOK — finish today (free / low-cost)

## Goal today

Green path: **download → Parquet → Snowflake load → dbt build → screenshots → teardown**.  
Airflow + Databricks if time; otherwise same day +1.

---

## 0) Answers needed from you (before cloud steps)

See `docs/QUESTIONS.md` — especially Snowflake + Databricks accounts.

---

## 1) Local setup (15 min)

```powershell
cd d:\IIMA\Portfolio\cfpb-data-platform
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:
- `CFPB_MODE=sample`
- `CFPB_SAMPLE_ROWS=200000` (or `50000` if slow network)

---

## 2) Ingest (20–40 min)

```powershell
python scripts\01_download_cfpb.py
python scripts\02_ingest_to_parquet.py
python scripts\03_validate_rowcounts.py
```

**Snapshot A:** terminal showing row counts + `data_quality/contracts.json`

---

## 3) Snowflake trial (30–45 min)

1. Create Snowflake trial (note credit expiry).
2. Worksheet → run in order:
   - `snowflake/01_database.sql`
   - `snowflake/02_stage.sql`
3. PUT Parquet (Snowsight **or** SnowSQL):

```sql
-- Adjust path to your machine
PUT file://D:/IIMA/Portfolio/cfpb-data-platform/data/parquet/complaints/year=*/part-000.parquet
  @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL
  AUTO_COMPRESS=FALSE
  OVERWRITE=TRUE;
```

If PUT with wildcards fails on Windows, PUT each `part-000.parquet` under each `year=` folder.

4. Run `snowflake/03_load.sql`
5. Confirm:

```sql
SELECT COUNT(*) FROM CFPB_DB.RAW.COMPLAINTS_RAW;
```

6. Put Snowflake secrets in `.env` then:

```powershell
python scripts\03_validate_rowcounts.py
```

**Must:** local count == Snowflake count.

**Snapshot B:** Snowflake worksheet `COUNT(*)`  
**Snapshot C:** `LIST @STG_COMPLAINTS_INTERNAL`  
**Snapshot D:** sample `SELECT * FROM V_COMPLAINTS LIMIT 20`

---

## 4) dbt (30–45 min)

```powershell
cd d:\IIMA\Portfolio\cfpb-data-platform\dbt_cfpb
copy profiles.yml.example profiles.yml
# OR rely on env_var in example — ensure .env loaded / env vars set in shell
$env:SNOWFLAKE_ACCOUNT="..."
$env:SNOWFLAKE_USER="..."
$env:SNOWFLAKE_PASSWORD="..."
dbt debug --profiles-dir .
dbt build --profiles-dir .
dbt docs generate --profiles-dir .
```

**Snapshot E:** `dbt build` green terminal  
**Snapshot F:** Snowflake showing `ANALYTICS` mart tables  
**Snapshot G:** open `target/index.html` docs (optional)

---

## 5) Airflow local (optional same day, 30–60 min)

Requires Docker Desktop.

```powershell
cd d:\IIMA\Portfolio\cfpb-data-platform\airflow
docker compose up -d
```

UI `http://localhost:8080` → admin/admin → unpause `cfpb_snowflake_dbt_pipeline`.

**Snapshot H:** DAG success graph  
**Snapshot I:** failed-test alert task log (optional: break a test once, show fail, fix)

---

## 6) Databricks Free Edition (30–45 min)

1. Create Free Edition workspace  
2. Upload `data/parquet/complaints` to FileStore/Volume  
3. Import `databricks/cfpb_lakehouse.py`  
4. Set `INPUT_PATH`, run cells  
5. Assert Delta count == Parquet count  

**Snapshot J:** notebook cell with counts  
**Snapshot K:** Delta table in catalog/DBFS

---

## 7) Document + teardown (20 min)

1. Fill `docs/SNAPSHOTS.md` checklist  
2. Fill `docs/EXPERIENCE.md` metrics + breakage notes  
3. Run `snowflake/99_teardown.sql`  
4. Delete Databricks cluster/tables/uploads  
5. `docker compose down -v`  
6. Delete S3 prefix if used  

**Never leave Snowflake warehouse running overnight.**
