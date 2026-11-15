select (select count(*) from raw_retail_transactions) as raw_rows,
       (select count(*) from stg_retail_transactions) as staged_rows,
       (select count(*) from stg_retail_transactions where disposition = 'accepted') as accepted_rows,
       (select count(*) from fact_sales_transactions) + (select count(*) from fact_returns) as fact_rows,
       (select count(*) from stg_retail_transactions where disposition = 'quarantined') as quarantined_rows,
       (select count(*) from stg_retail_transactions where disposition = 'duplicate') as duplicate_rows;
