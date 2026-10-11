# PUT helper (Windows)

From repo root, list files to upload:

```powershell
Get-ChildItem -Recurse .\data\parquet\complaints\*.parquet | Select-Object FullName
```

In Snowflake worksheet / SnowSQL, for each file:

```sql
PUT file://D:/IIMA/Portfolio/cfpb-data-platform/data/parquet/complaints/year=2023/part-000.parquet
  @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL
  AUTO_COMPRESS = FALSE
  OVERWRITE = TRUE;
```

Use forward slashes in `file://` URIs.

Then run `snowflake/03_load.sql`.

If VARIANT keys don't match (`SRC:"Complaint ID"` empty), inspect:

```sql
SELECT SRC FROM CFPB_DB.RAW.COMPLAINTS_RAW LIMIT 1;
```

Adjust `V_COMPLAINTS` column expressions to the actual key names (Parquet often lowercases / sanitizes headers).
