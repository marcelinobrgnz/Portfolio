
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        product as value_field,
        count(*) as n_records

    from CFPB_DB.ANALYTICS_staging.stg_complaints
    group by product

)

select *
from all_values
where value_field not in (
    'Credit reporting, credit repair services, or other personal consumer reports','Credit card or prepaid card','Debt collection','Checking or savings account','Mortgage','Vehicle loan or lease','Student loan','Money transfer, virtual currency, or money service','Payday loan, title loan, personal loan, or advance','Credit reporting','Credit card','Bank account or service','Consumer Loan','Prepaid card','Other financial service','Payday loan','Money transfers','Virtual currency'
)



  
  
      
    ) dbt_internal_test