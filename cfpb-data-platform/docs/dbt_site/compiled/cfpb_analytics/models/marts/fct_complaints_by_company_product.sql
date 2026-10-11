

select
    company,
    product,
    count(*) as complaint_count,
    count_if(timely_response_flag = true) as timely_yes,
    count_if(timely_response_flag = false) as timely_no,
    count_if(consumer_disputed_flag = true) as disputed,
    min(date_received) as first_complaint_date,
    max(date_received) as last_complaint_date
from CFPB_DB.ANALYTICS_staging.stg_complaints
where company is not null
  and product is not null
group by 1, 2