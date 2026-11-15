with fact as (select coalesce(sum(amount), 0) as value from {{ ref('stg_all_transactions') }}),
mart as (select coalesce(sum(net_sales), 0) as value from {{ ref('mart_daily_sales') }})
select fact.value, mart.value from fact cross join mart where abs(fact.value - mart.value) > 0.01
