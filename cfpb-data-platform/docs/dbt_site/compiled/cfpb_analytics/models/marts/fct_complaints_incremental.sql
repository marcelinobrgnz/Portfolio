

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
from CFPB_DB.ANALYTICS_staging.stg_complaints

