with baskets as (
 select distinct invoice, stock_code from fact_sales_transactions
 where stock_code in (select stock_code from dim_product where category = 'merchandise')
), pairs as (
 select a.stock_code as antecedent, b.stock_code as consequent, count(*) as pair_count
 from baskets a join baskets b on a.invoice = b.invoice and a.stock_code <> b.stock_code
 group by a.stock_code, b.stock_code
), singles as (select stock_code, count(*) as basket_count from baskets group by stock_code),
totals as (select count(distinct invoice) as n from baskets)
select p.*, 1.0 * p.pair_count / t.n as support,
 1.0 * p.pair_count / a.basket_count as confidence,
 1.0 * p.pair_count * t.n / (a.basket_count * b.basket_count) as lift
from pairs p join singles a on a.stock_code = p.antecedent
join singles b on b.stock_code = p.consequent cross join totals t
where p.pair_count >= 2 order by lift desc;
