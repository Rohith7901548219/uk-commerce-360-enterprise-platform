with contribution as (
 select customer_key, count(distinct invoice) as orders, sum(amount) as revenue
 from fact_sales_transactions where customer_key is not null group by customer_key
)
select *, dense_rank() over(order by revenue desc) as revenue_rank,
 revenue / nullif(sum(revenue) over(), 0) as identifiable_gross_revenue_share,
 sum(revenue) over(order by revenue desc, customer_key rows unbounded preceding)
 / nullif(sum(revenue) over(), 0) as cumulative_share
from contribution order by revenue desc;
