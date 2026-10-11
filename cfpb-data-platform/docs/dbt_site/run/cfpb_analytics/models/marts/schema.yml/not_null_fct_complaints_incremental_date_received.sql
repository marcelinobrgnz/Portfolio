
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date_received
from CFPB_DB.ANALYTICS_marts.fct_complaints_incremental
where date_received is null



  
  
      
    ) dbt_internal_test