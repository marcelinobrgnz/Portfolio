
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select complaint_count
from CFPB_DB.ANALYTICS_marts.fct_complaints_by_product_month
where complaint_count is null



  
  
      
    ) dbt_internal_test