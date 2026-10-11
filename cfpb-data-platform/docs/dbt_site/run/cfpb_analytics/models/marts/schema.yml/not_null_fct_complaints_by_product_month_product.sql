
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product
from CFPB_DB.ANALYTICS_marts.fct_complaints_by_product_month
where product is null



  
  
      
    ) dbt_internal_test