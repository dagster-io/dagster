{{
  config(
    materialized='incremental'
  )
}}

with max_order_date as (
    select
      max(order_date) as max_order_date
    from {{ this }}
)

select
    order_id,
    order_date
from {{ ref('orders') }}

{% if is_incremental() %}

where order_date >= (select max_order_date from max_order_date)

{% endif %}
