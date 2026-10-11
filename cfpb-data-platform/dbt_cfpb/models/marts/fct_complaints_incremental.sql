{{
  config(
    materialized='incremental',
    unique_key='complaint_id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
  )
}}

-- Incremental fact: new/updated complaints only (interview favorite).
-- Full refresh on first run; thereafter merge by complaint_id.

select
    complaint_id,
    date_received,
    product,
    sub_product,
    issue,
    company,
    state,
    submitted_via,
    timely_response_flag,
    consumer_disputed_flag,
    _loaded_at,
    current_timestamp() as _dbt_updated_at
from {{ ref('stg_complaints') }}

{% if is_incremental() %}
  where _loaded_at > (select coalesce(max(_loaded_at), '1900-01-01'::timestamp_ntz) from {{ this }})
{% endif %}
