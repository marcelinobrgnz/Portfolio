import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when, lit, size, split

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_INPUT', 'S3_OUTPUT'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read raw items metadata
items_df = spark.read.parquet(args['S3_INPUT'])

# Transform to items table
# Align item identifier with events table by using parent_asin as item_id
# Note: metadata schema uses `categories` (plural), `main_category`, `price`, `store`, `author`, etc.
items_processed = items_df.select(
    col("parent_asin").alias("item_id"),
    col("title"),
    col("categories").alias("category_raw"),
    col("price").alias("price_raw"),
    col("main_category"),
    col("store"),
    col("author")
).withColumn(
    "price_bucket",
    when(col("price_raw").isNull(), "unknown")
    .when(col("price_raw") < 10, "low")
    .when(col("price_raw") < 50, "medium")
    .when(col("price_raw") < 200, "high")
    .otherwise("premium")
).withColumn(
    # Use presence of store as a proxy flag (kept column name `has_brand` for downstream compatibility)
    "has_brand",
    when(col("store").isNotNull(), True).otherwise(False)
)

# Write to S3
items_processed.write.mode("overwrite").parquet(args['S3_OUTPUT'])

job.commit()