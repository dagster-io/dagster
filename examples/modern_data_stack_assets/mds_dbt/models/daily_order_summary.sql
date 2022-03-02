select
        date_trunc('d', oc.order_time::timestamp) as order_date,
        sum(oc.order_value) as total_value,
        count(*) as num_orders
from
        {{ ref("orders_cleaned") }} oc
        join
        {{ ref("users_augmented") }} ua
        on oc.user_id = ua.user_id
where not ua.is_bot
group by 1 order by 1
