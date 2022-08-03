select
        company,
        sum(n_orders) as n_orders,
        sum(total_revenue) as total_revenue
from {{ ref("company_stats") }}
group by 1