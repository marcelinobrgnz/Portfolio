
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date_received
from CFPB_DB.ANALYTICS_staging.stg_complaints
where date_received is null



  
  
      
    ) dbt_internal_test