with daily as (
 select date_key, sum(amount) as revenue from (
  select date_key, amount from fact_sales_transactions
  union all select date_key, amount from fact_returns
 ) transactions group by date_key
)
select date_key, revenue,
 sum(revenue) over(order by date_key rows between 6 preceding and current row) as rolling_7_observed_days,
 avg(revenue) over(order by date_key rows between 6 preceding and current row) as moving_average_7_observed_days,
 revenue - lag(revenue, 1) over(order by date_key) as change_from_prior_observed_day
from daily order by date_key;
