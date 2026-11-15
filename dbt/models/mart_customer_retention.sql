select cohort, period, customers, cohort_size, retention_rate
from {{ ref('mart_customer_cohorts') }}
