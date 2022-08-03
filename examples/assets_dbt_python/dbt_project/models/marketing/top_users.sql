select
        o.user_id,
        sum(o.order_total) as total_revenue,
        sum(o.order_total) / max(c.total_revenue) as pct_revenue
from
        {{ ref("orders_augmented") }} o left join
        {{ ref("company_perf") }} c on o.company = c.company
group by 1
