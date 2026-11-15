select transaction_id, invoice, customer_key, stock_code, country, date_key, event_time, quantity, amount,
       'sale' as transaction_type from {{ source('warehouse', 'fact_sales_transactions') }}
union all
select transaction_id, invoice, customer_key, stock_code, country, date_key, event_time, quantity, amount,
       'return' as transaction_type from {{ source('warehouse', 'fact_returns') }}
