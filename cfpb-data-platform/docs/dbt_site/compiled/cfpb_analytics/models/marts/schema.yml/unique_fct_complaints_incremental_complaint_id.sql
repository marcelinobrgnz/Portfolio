
    
    

select
    complaint_id as unique_field,
    count(*) as n_records

from CFPB_DB.ANALYTICS_marts.fct_complaints_incremental
where complaint_id is not null
group by complaint_id
having count(*) > 1


