-- 03_load.sql
-- RAW landing table + COPY INTO from internal stage.
-- Peak DE: VARIANT landing for schema drift resilience, then typed view for dbt.

USE DATABASE CFPB_DB;
USE SCHEMA RAW;
USE WAREHOUSE CFPB_WH;

CREATE OR REPLACE TABLE CFPB_DB.RAW.COMPLAINTS_RAW (
  SRC VARIANT,
  FILENAME STRING,
  FILE_ROW_NUMBER NUMBER,
  LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Landing: one VARIANT per Parquet row + lineage columns';

-- After: PUT file://<local>/data/parquet/complaints/*.parquet @STG_COMPLAINTS_INTERNAL AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- Example (SnowSQL):
-- PUT file://D:/IIMA/Portfolio/cfpb-data-platform/data/parquet/complaints/*.parquet @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

COPY INTO CFPB_DB.RAW.COMPLAINTS_RAW (SRC, FILENAME, FILE_ROW_NUMBER)
FROM (
  SELECT
    $1,
    METADATA$FILENAME,
    METADATA$FILE_ROW_NUMBER
  FROM @CFPB_DB.RAW.STG_COMPLAINTS_INTERNAL
)
FILE_FORMAT = (TYPE = PARQUET)
ON_ERROR = 'ABORT_STATEMENT'
FORCE = TRUE;

-- Reconciliation — must match scripts/03_validate_rowcounts.py parquet count
SELECT COUNT(*) AS snowflake_rows FROM CFPB_DB.RAW.COMPLAINTS_RAW;

-- Typed projection for dbt (column names match CFPB export; adjust if sample schema differs)
CREATE OR REPLACE VIEW CFPB_DB.RAW.V_COMPLAINTS AS
SELECT
  SRC:"Complaint ID"::STRING            AS complaint_id,
  SRC:"Date received"::STRING           AS date_received,
  SRC:"Product"::STRING                 AS product,
  SRC:"Sub-product"::STRING             AS sub_product,
  SRC:"Issue"::STRING                   AS issue,
  SRC:"Sub-issue"::STRING               AS sub_issue,
  SRC:"Consumer complaint narrative"::STRING AS consumer_complaint_narrative,
  SRC:"Company public response"::STRING AS company_public_response,
  SRC:"Company"::STRING                 AS company,
  SRC:"State"::STRING                   AS state,
  SRC:"ZIP code"::STRING                AS zip_code,
  SRC:"Tags"::STRING                    AS tags,
  SRC:"Consumer consent provided?"::STRING AS consumer_consent_provided,
  SRC:"Submitted via"::STRING           AS submitted_via,
  SRC:"Date sent to company"::STRING    AS date_sent_to_company,
  SRC:"Company response to consumer"::STRING AS company_response_to_consumer,
  SRC:"Timely response?"::STRING        AS timely_response,
  SRC:"Consumer disputed?"::STRING      AS consumer_disputed,
  FILENAME,
  FILE_ROW_NUMBER,
  LOADED_AT
FROM CFPB_DB.RAW.COMPLAINTS_RAW;

SELECT COUNT(*) AS view_rows FROM CFPB_DB.RAW.V_COMPLAINTS;
SELECT COUNT(DISTINCT complaint_id) AS distinct_ids FROM CFPB_DB.RAW.V_COMPLAINTS;
