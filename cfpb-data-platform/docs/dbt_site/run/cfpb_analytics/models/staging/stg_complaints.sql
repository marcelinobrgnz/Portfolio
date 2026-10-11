
  create or replace   view CFPB_DB.ANALYTICS_staging.stg_complaints
  
   as (
    

-- Staging: clean types, trim, standardized flags
with src as (
    select * from CFPB_DB.RAW.V_COMPLAINTS
)

select
    complaint_id,
    try_to_date(date_received) as date_received,
    nullif(trim(product), '') as product,
    nullif(trim(sub_product), '') as sub_product,
    nullif(trim(issue), '') as issue,
    nullif(trim(sub_issue), '') as sub_issue,
    consumer_complaint_narrative,
    nullif(trim(company), '') as company,
    nullif(trim(state), '') as state,
    nullif(trim(zip_code), '') as zip_code,
    nullif(trim(submitted_via), '') as submitted_via,
    try_to_date(date_sent_to_company) as date_sent_to_company,
    nullif(trim(company_response_to_consumer), '') as company_response_to_consumer,
    case
        when lower(coalesce(timely_response, '')) in ('yes', 'y', 'true', '1') then true
        when lower(coalesce(timely_response, '')) in ('no', 'n', 'false', '0') then false
        else null
    end as timely_response_flag,
    case
        when lower(coalesce(consumer_disputed, '')) in ('yes', 'y', 'true', '1') then true
        when lower(coalesce(consumer_disputed, '')) in ('no', 'n', 'false', '0') then false
        else null
    end as consumer_disputed_flag,
    filename as _source_file,
    loaded_at as _loaded_at
from src
where complaint_id is not null
  );

