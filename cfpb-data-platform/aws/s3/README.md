# Optional AWS helpers — keep empty S3_BUCKET for free local-only day.

## Sync Parquet to S3 (only if needed for screenshots)

```powershell
cd d:\IIMA\Portfolio\cfpb-data-platform
copy .env.example .env
# set S3_BUCKET=your-temp-bucket
python scripts/02_ingest_to_parquet.py
```

## Teardown S3 prefix

```powershell
aws s3 rm s3://YOUR_BUCKET/cfpb/parquet --recursive --region eu-west-1
```

Prefer **Snowflake internal stage + PUT** on portfolio day — $0 AWS required.
