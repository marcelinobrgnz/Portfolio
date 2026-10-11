
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    complaint_id as unique_field,
    count(*) as n_records

from CFPB_DB.RAW.V_COMPLAINTS
where complaint_id is not null
group by complaint_id
having count(*) > 1



  
  
      
    ) dbt_internal_test