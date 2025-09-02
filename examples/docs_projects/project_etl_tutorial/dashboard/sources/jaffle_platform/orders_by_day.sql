select
  order_date, sum(amount) as total_amount, count(*) as order_count
from orders
group by 1
order by 1 asc