with customers as (

    select * from {{ ref('stg_customers') }}

),

customer_orders as (

    select * from {{ ref('customer_orders') }}

),

customer_payments as (

    select * from {{ ref('customer_payments') }}

),

final as (

    select
        customers.customer_id,
        customer_orders.first_order,
        customer_orders.most_recent_order,
        customer_orders.number_of_orders,
        customer_payments.total_amount as customer_lifetime_value

    from customers

    left join customer_orders using (customer_id)

    left join customer_payments using (customer_id)

)

select * from final
