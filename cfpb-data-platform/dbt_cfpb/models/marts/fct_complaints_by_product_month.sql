{{ config(materialized='table') }}

select
    date_trunc('month', date_received) as month_start,
    product,
    count(*) as complaint_count,
    count(distinct company) as company_count,
    count_if(timely_response_flag = false) as untimely_count,
    count_if(consumer_disputed_flag = true) as disputed_count,
    round(count_if(consumer_disputed_flag = true) / nullif(count(*), 0), 4) as dispute_rate
from {{ ref('stg_complaints') }}
where date_received is not null
  and product is not null
group by 1, 2
