with months as (
 select date_trunc('month', date_key)::date as month, sum(amount) as net_sales
 from (select date_key, amount from fact_sales_transactions union all select date_key, amount from fact_returns) t
 group by 1
)
select current.month, current.net_sales, prior.net_sales as previous_year_net_sales,
 (current.net_sales - prior.net_sales) / nullif(prior.net_sales, 0) as yoy_change
from months current left join months prior on prior.month = (current.month - interval '1 year')::date
order by current.month;
