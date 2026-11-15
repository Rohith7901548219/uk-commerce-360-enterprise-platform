with customer_orders as (
 select customer_key, max(date_key) as last_purchase, count(distinct invoice) as frequency,
        sum(amount) as monetary
 from {{ source('warehouse', 'fact_sales_transactions') }}
 where customer_key is not null group by customer_key
), scored as (
 select *, ((select max(date_key) + 1 from {{ source('warehouse', 'fact_sales_transactions') }}) - last_purchase) as recency,
        ceil(cume_dist() over(order by last_purchase) * 5)::int as recency_score,
        ceil(cume_dist() over(order by frequency) * 5)::int as frequency_score,
        ceil(cume_dist() over(order by monetary) * 5)::int as monetary_score
 from customer_orders
)
select *, case when recency_score >= 4 and frequency_score >= 4 then 'Champions'
 when recency_score <= 2 and monetary_score >= 4 then 'At risk · high value'
 when frequency >= 3 then 'Loyal' when recency_score >= 4 then 'New / recent' else 'Developing' end as segment
from scored
