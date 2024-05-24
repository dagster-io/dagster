with orders_1 as (

    select * from {{ ref('orders') }}

),

orders_2 as (

    select * from {{ ref('orders') }}

),

final as (

    select
        orders_1.amount + orders_2.amount as amount_2x

    from orders_1

    left join orders_2
        on orders_1.order_id = orders_2.order_id

)

select * from final
