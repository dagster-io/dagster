select
        date as order_date,
        n_orders as num_orders
from {{ ref("order_stats") }}
-- this doesn't really do anything