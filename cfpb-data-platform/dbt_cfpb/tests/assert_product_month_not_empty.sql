-- Singular test: mart row count must be > 0 after build
select 1
from {{ ref('fct_complaints_by_product_month') }}
having count(*) = 0
