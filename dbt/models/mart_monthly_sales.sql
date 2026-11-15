select date_trunc('month', date_key)::date as month,
       sum(gross_sales) as gross_sales, sum(returns) as returns, sum(net_sales) as net_sales,
       sum(orders) as orders
from {{ ref('mart_daily_sales') }} group by 1
