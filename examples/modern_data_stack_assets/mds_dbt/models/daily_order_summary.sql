SELECT * FROM {{ ref("orders_cleaned") }}
UNION SELECT * FROM {{ ref("users_augmented") }}
-- select
--        date_trunc('d', order_time) as order_day,
--        sum(order_amount)
--from {{ ref("orders_cleaned") }} oc join {{ ref("users_augmented") }} u
--on oc.user_id = u.user_id
--where not u.is_spam
