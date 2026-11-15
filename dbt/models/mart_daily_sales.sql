{{ config(materialized='incremental', unique_key='date_key', incremental_strategy='delete+insert') }}
select date_key,
       sum(case when transaction_type = 'sale' then amount else 0 end) as gross_sales,
       -sum(case when transaction_type = 'return' then amount else 0 end) as returns,
       sum(amount) as net_sales,
       count(distinct case when transaction_type = 'sale' then invoice end) as orders
from {{ ref('stg_all_transactions') }}
{% if is_incremental() %}
-- A 31-day overlap handles late arrivals. Older backfills require --full-refresh.
where date_key >= (select coalesce(max(date_key), date '1900-01-01') - interval '31 day' from {{ this }})
{% endif %}
group by date_key
