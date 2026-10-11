"""
CFPB lakehouse path on Databricks Free Edition.

Peak DE demos:
- Spark read of partitioned Parquet
- Delta Lake table write + count reconciliation
- Product/month mart equivalent to dbt fct
"""

# Databricks notebook source
# MAGIC %md
# MAGIC # CFPB Lakehouse (Databricks)
# MAGIC Same dataset as Snowflake/dbt path — Delta instead of Snowflake tables.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("INPUT_PATH", "/FileStore/cfpb/complaints")
dbutils.widgets.text("DELTA_PATH", "/FileStore/cfpb/delta/complaints")

INPUT_PATH = dbutils.widgets.get("INPUT_PATH")
DELTA_PATH = dbutils.widgets.get("DELTA_PATH")

# COMMAND ----------

df = spark.read.parquet(INPUT_PATH)
row_count = df.count()
print(f"parquet_rows={row_count}")
print(f"columns={df.columns}")

# COMMAND ----------

# Normalize CFPB headers (spaces / case)
rename_map = {}
for c in df.columns:
    key = c.strip().lower().replace(" ", "_").replace("?", "").replace("-", "_")
    rename_map[c] = key
df_n = df
for old, new in rename_map.items():
    if old != new:
        df_n = df_n.withColumnRenamed(old, new)

# COMMAND ----------

(
    df_n.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(DELTA_PATH)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS cfpb_complaints_delta USING DELTA LOCATION '{DELTA_PATH}'")

delta_count = spark.read.format("delta").load(DELTA_PATH).count()
print(f"delta_rows={delta_count}")
assert delta_count == row_count, "Delta count must match Parquet count"

# COMMAND ----------

cols = set(df_n.columns)
product_col = "product" if "product" in cols else None
date_col = "date_received" if "date_received" in cols else None

if product_col and date_col:
    mart = (
        df_n.withColumn("month_start", F.date_trunc("month", F.to_date(F.col(date_col))))
        .groupBy(product_col, "month_start")
        .agg(F.count(F.lit(1)).alias("complaint_count"))
        .orderBy(F.desc("complaint_count"))
    )
    mart_path = "/FileStore/cfpb/delta/fct_complaints_by_product_month"
    mart.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(mart_path)
    print(f"mart_rows={mart.count()} path={mart_path}")
    display(mart.limit(50))
else:
    print(f"Skip mart — missing columns. Have={sorted(cols)[:30]}")

# COMMAND ----------

print("DONE Databricks lakehouse path")
