
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: mart row count must be > 0 after build
select 1
from CFPB_DB.ANALYTICS_marts.fct_complaints_by_product_month
having count(*) = 0
  
  
      
    ) dbt_internal_test