
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select complaint_id
from CFPB_DB.ANALYTICS_marts.fct_complaints_incremental
where complaint_id is null



  
  
      
    ) dbt_internal_test