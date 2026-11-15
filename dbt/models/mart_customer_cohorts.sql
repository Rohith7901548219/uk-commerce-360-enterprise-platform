with customer_months as (
 select distinct customer_key, date_trunc('month', date_key)::date as month
 from {{ source('warehouse', 'fact_sales_transactions') }} where customer_key is not null
), cohorts as (
 select *, min(month) over(partition by customer_key) as cohort from customer_months
), counts as (
 select cohort, (extract(year from month)::int - extract(year from cohort)::int) * 12
     + extract(month from month)::int - extract(month from cohort)::int as period,
 count(distinct customer_key) as customers
 from cohorts group by cohort, month
)
select *, max(customers) filter(where period = 0) over(partition by cohort) as cohort_size,
 customers::numeric / nullif(max(customers) filter(where period = 0) over(partition by cohort), 0) as retention_rate
from counts
