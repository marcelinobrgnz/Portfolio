
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date_received
from CFPB_DB.RAW.V_COMPLAINTS
where date_received is null



  
  
      
    ) dbt_internal_test