with country_products as (
 select country, stock_code, sum(amount) as revenue, sum(quantity) as units
 from fact_sales_transactions group by country, stock_code
)
select *, dense_rank() over(partition by country order by revenue desc) as market_rank
from country_products order by country, market_rank;
