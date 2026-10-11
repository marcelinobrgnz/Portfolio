# TEARDOWN — same day (cost control)

## Snowflake

Run `snowflake/99_teardown.sql` as ACCOUNTADMIN.

Confirm:

```sql
SHOW DATABASES LIKE 'CFPB%';
SHOW WAREHOUSES LIKE 'CFPB%';
```

Both should return no portfolio objects.

Suspend any other warehouses you started in the UI.

## Databricks

- Drop Delta tables / paths created (`/FileStore/cfpb/...`)
- Terminate / delete cluster
- Remove uploaded files

## Airflow

```powershell
cd d:\IIMA\Portfolio\cfpb-data-platform\airflow
docker compose down -v
```

## AWS (only if used)

```powershell
aws s3 rm s3://YOUR_BUCKET/cfpb/parquet --recursive --region eu-west-1
```

## Local secrets

- Clear `.env` password or delete `.env` after run
- Do not commit `profiles.yml` with embedded passwords

## After teardown

Tick snapshot **M** in `SNAPSHOTS.md` and note date/time in `EXPERIENCE.md`.
