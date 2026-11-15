select t.stock_code, p.description, p.category,
 sum(case when quantity > 0 then quantity else 0 end) as units_sold,
 -sum(case when quantity < 0 then quantity else 0 end) as units_returned,
 sum(amount) as net_sales,
 dense_rank() over(order by sum(amount) desc) as revenue_rank
from {{ ref('stg_all_transactions') }} t
join {{ source('warehouse', 'dim_product') }} p on p.stock_code = t.stock_code
group by t.stock_code, p.description, p.category
