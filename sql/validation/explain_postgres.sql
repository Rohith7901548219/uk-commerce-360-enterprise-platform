-- Execute only in PostgreSQL. Compare plans before changing indexes; retain measured output.
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT customer_key, sum(amount) FROM fact_sales_transactions
WHERE date_key >= DATE '2011-09-01' GROUP BY customer_key;
