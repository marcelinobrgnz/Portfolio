-- 02b_external_stage_s3.sql
-- S3 external stage (preferred for full dataset). Credentials injected by bootstrap script.

USE DATABASE CFPB_DB;
USE SCHEMA RAW;

-- Placeholder replaced at runtime by scripts/04_snowflake_bootstrap.py
-- CREATE OR REPLACE STAGE CFPB_DB.RAW.STG_COMPLAINTS_S3 ...
