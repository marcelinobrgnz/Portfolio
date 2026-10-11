
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select complaint_id
from CFPB_DB.ANALYTICS_staging.stg_complaints
where complaint_id is null



  
  
      
    ) dbt_internal_test