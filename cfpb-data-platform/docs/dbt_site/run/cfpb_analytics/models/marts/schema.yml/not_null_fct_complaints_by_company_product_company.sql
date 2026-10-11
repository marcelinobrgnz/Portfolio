
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select company
from CFPB_DB.ANALYTICS_marts.fct_complaints_by_company_product
where company is null



  
  
      
    ) dbt_internal_test