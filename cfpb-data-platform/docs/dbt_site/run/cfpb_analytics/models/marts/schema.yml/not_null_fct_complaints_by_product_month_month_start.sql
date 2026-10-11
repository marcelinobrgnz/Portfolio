
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select month_start
from CFPB_DB.ANALYTICS_marts.fct_complaints_by_product_month
where month_start is null



  
  
      
    ) dbt_internal_test