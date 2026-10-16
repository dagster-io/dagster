{% snapshot orders_snapshot %}

{{
    config(
        target_schema='main',
        unique_key='order_id',
        strategy='check',
        check_cols=['status'],
    )
}}

select order_id, customer_id, status
from {{ ref('orders') }}

{% endsnapshot %}
