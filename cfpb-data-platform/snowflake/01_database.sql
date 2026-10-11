-- 01_database.sql
-- Run in Snowflake worksheet as ACCOUNTADMIN (trial).
-- Peak DE: separate RAW vs ANALYTICS, sized warehouse, comment everything.

CREATE WAREHOUSE IF NOT EXISTS CFPB_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'CFPB portfolio — suspend fast to protect trial credits';

CREATE DATABASE IF NOT EXISTS CFPB_DB
  COMMENT = 'CFPB consumer complaints lakehouse portfolio';

CREATE SCHEMA IF NOT EXISTS CFPB_DB.RAW
  COMMENT = 'Immutable landing zone — COPY INTO targets';

CREATE SCHEMA IF NOT EXISTS CFPB_DB.ANALYTICS
  COMMENT = 'dbt-managed analytics objects (optional target schema)';

-- File format for Parquet loads
CREATE OR REPLACE FILE FORMAT CFPB_DB.RAW.FF_PARQUET
  TYPE = PARQUET
  COMPRESSION = AUTO;

-- Optional: CSV fallback if you load CSV instead of Parquet
CREATE OR REPLACE FILE FORMAT CFPB_DB.RAW.FF_CSV
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NA', 'N/A', 'null')
  EMPTY_FIELD_AS_NULL = TRUE
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;
