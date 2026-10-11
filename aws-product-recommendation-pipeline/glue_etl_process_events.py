import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, when, lit
from pyspark.sql.types import IntegerType, StringType, TimestampType

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_INPUT', 'S3_OUTPUT'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read raw parquet from S3 (train/valid/test splits under the base path)
input_base = args['S3_INPUT']  # e.g. s3://amazon-electronics/raw/amazon_reviews/electronics/parquet/interactions/
raw_df = spark.read.parquet(
    input_base + "train/",
    input_base + "valid/",
    input_base + "test/"
)

# Transform to events table based on 0core_timestamp_w_his_Electronics schema
# Actual columns include: user_id, history, rating, timestamp, parent_asin, ...
# We treat parent_asin as the item identifier.
events_df = raw_df.select(
    col("user_id").alias("user_id"),
    col("parent_asin").alias("item_id"),
    col("rating").alias("rating"),
    col("timestamp").alias("timestamp")
).withColumn(
    "event_type",
    when(col("rating") >= 4, "positive_rating")
    .when(col("rating") >= 3, "neutral_rating")
    .otherwise("negative_rating")
).withColumn(
    "date",
    to_date(col("timestamp"))
)

# Data quality checks
print(f"Total events: {events_df.count()}")
print(f"Distinct users: {events_df.select('user_id').distinct().count()}")
print(f"Distinct items: {events_df.select('item_id').distinct().count()}")

# Write partitioned by date
events_df.write.mode("overwrite").partitionBy("date").parquet(args['S3_OUTPUT'])

job.commit()