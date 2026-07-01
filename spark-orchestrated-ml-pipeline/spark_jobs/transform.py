"""PySpark batch transforms: wine features (P1) + NYC Taxi volume ETL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

# Allow `python spark_jobs/transform.py` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spark_jobs.helpers import (  # noqa: E402
    WINE_BOUNDS,
    WINE_TYPE_MAP,
    normalize_wine_column,
)


def create_spark(app_name: str, master: str) -> SparkSession:
  builder = (
      SparkSession.builder.appName(app_name)
      .master(master)
      .config("spark.sql.shuffle.partitions", "8")
      .config("spark.sql.parquet.compression.codec", "snappy")
  )
  # S3 access when running with hadoop-aws on classpath (Docker / EMR)
  builder = builder.config(
      "spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
  )
  return builder.getOrCreate()


def _rename_wine_columns(df: DataFrame) -> DataFrame:
  for col in df.columns:
    df = df.withColumnRenamed(col, normalize_wine_column(col))
  return df


def transform_wine(spark: SparkSession, input_path: str, output_path: str) -> dict:
  """Clean UCI wine CSVs, engineer ratios, write partitioned Parquet."""
  df = spark.read.option("header", True).option("sep", ";").csv(input_path)
  df = _rename_wine_columns(df)

  if "wine_type" not in df.columns:
    df = df.withColumn(
        "wine_type",
        F.when(F.input_file_name().contains("red"), F.lit("red")).otherwise(F.lit("white")),
    )

  mapping = F.create_map([F.lit(x) for kv in WINE_TYPE_MAP.items() for x in kv])
  df = df.withColumn("wine_type", mapping[F.col("wine_type")])

  for column, (low, high) in WINE_BOUNDS.items():
    df = df.filter((F.col(column) >= low) & (F.col(column) <= high))

  df = (
      df.withColumn(
          "total_acidity",
          F.col("fixed_acidity") + F.col("volatile_acidity") + F.col("citric_acid"),
      )
      .withColumn(
          "free_to_total_so2_ratio",
          F.col("free_sulfur_dioxide") / F.greatest(F.col("total_sulfur_dioxide"), F.lit(1.0)),
      )
      .withColumn(
          "alcohol_density_ratio",
          F.col("alcohol") / F.col("density"),
      )
  )

  raw_count = df.count()
  (
      df.write.mode("overwrite")
      .partitionBy("wine_type")
      .parquet(output_path)
  )

  return {
      "dataset": "wine",
      "input_path": input_path,
      "output_path": output_path,
      "row_count": raw_count,
      "partitions": df.select("wine_type").distinct().count(),
  }


def transform_taxi(spark: SparkSession, input_path: str, output_path: str) -> dict:
  """NYC Yellow Taxi: clean trips, window aggregates, Parquet feature store."""
  df = spark.read.parquet(input_path)

  df = (
      df.filter(F.col("trip_distance") > 0)
      .filter(F.col("fare_amount") > 0)
      .filter(F.col("fare_amount") < 500)
      .filter(F.col("passenger_count").between(1, 6))
      .withColumn("pickup_ts", F.to_timestamp("tpep_pickup_datetime"))
      .withColumn("dropoff_ts", F.to_timestamp("tpep_dropoff_datetime"))
      .filter(F.col("pickup_ts").isNotNull())
      .withColumn(
          "trip_duration_min",
          (F.unix_timestamp("dropoff_ts") - F.unix_timestamp("pickup_ts")) / 60.0,
      )
      .filter((F.col("trip_duration_min") > 0) & (F.col("trip_duration_min") < 180))
      .withColumn("pickup_hour", F.hour("pickup_ts"))
      .withColumn("pickup_dow", F.dayofweek("pickup_ts"))
      .withColumn("pickup_date", F.to_date("pickup_ts"))
      .withColumn("fare_per_mile", F.col("fare_amount") / F.col("trip_distance"))
  )

  zone_window = Window.partitionBy("PULocationID", "pickup_hour")
  df = (
      df.withColumn("zone_avg_fare", F.avg("fare_amount").over(zone_window))
      .withColumn("zone_trip_count", F.count("*").over(zone_window))
      .withColumn("zone_avg_distance", F.avg("trip_distance").over(zone_window))
  )

  feature_cols = [
      "pickup_hour",
      "pickup_dow",
      "trip_distance",
      "trip_duration_min",
      "passenger_count",
      "fare_per_mile",
      "zone_avg_fare",
      "zone_trip_count",
      "zone_avg_distance",
      "PULocationID",
      "DOLocationID",
      "fare_amount",
  ]
  features = df.select(*feature_cols, "pickup_date")

  row_count = features.count()
  (
      features.write.mode("overwrite")
      .partitionBy("pickup_date")
      .parquet(output_path)
  )

  return {
      "dataset": "taxi",
      "input_path": input_path,
      "output_path": output_path,
      "row_count": row_count,
      "partitions": features.select("pickup_date").distinct().count(),
  }


def main() -> None:
  parser = argparse.ArgumentParser(description="PySpark feature engineering job")
  parser.add_argument("--dataset", choices=["wine", "taxi"], required=True)
  parser.add_argument("--input", required=True, help="Raw input path (CSV dir or Parquet)")
  parser.add_argument("--output", required=True, help="Feature store output (local or s3a://)")
  parser.add_argument("--master", default="local[*]")
  parser.add_argument("--metrics-file", default="")
  args = parser.parse_args()

  spark = create_spark(f"feature-etl-{args.dataset}", args.master)
  try:
    if args.dataset == "wine":
      stats = transform_wine(spark, args.input, args.output)
    else:
      stats = transform_taxi(spark, args.input, args.output)

    print(json.dumps(stats, indent=2))
    if args.metrics_file:
      Path(args.metrics_file).parent.mkdir(parents=True, exist_ok=True)
      Path(args.metrics_file).write_text(json.dumps(stats, indent=2), encoding="utf-8")
  finally:
    spark.stop()


if __name__ == "__main__":
  main()
