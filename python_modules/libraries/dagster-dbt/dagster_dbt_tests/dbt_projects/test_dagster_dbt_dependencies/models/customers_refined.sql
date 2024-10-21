with customers as (

    select * from {{ ref('jaffle_shop', 'customers') }}

)

select * from customers
