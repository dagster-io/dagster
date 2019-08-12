{% set payment_methods = ['credit_card', 'coupon', 'bank_transfer', 'gift_card'] %}

with orders as (

    select * from {{ ref('stg_orders') }}

),

order_payments as (

    select * from {{ ref('order_payments') }}

),

final as (

    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        orders.status,

        {% for payment_method in payment_methods -%}

        order_payments.{{payment_method}}_amount,

        {% endfor -%}

        order_payments.total_amount as amount

    from orders

    left join order_payments using (order_id)

)

select * from final
