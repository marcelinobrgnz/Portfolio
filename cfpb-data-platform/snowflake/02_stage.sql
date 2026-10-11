-- 02_stage.sql
-- Internal stage for PUT from local machine (trial-friendly, no S3 required).
-- If using S3 external stage instead, see 02b_external_stage_s3.sql.example

USE DATABASE CFPB_DB;
USE SCHEMA RAW;

CREATE OR REPLACE STAGE CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL
  FILE_FORMAT = CFPB_DB.RAW.FF_PARQUET
  COMMENT = 'Internal stage — PUT local Parquet then COPY INTO';

-- Inspect
-- LIST @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL;
