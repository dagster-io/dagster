{{ config(materialized='table', schema='bronze') }}

select
    customer_id,
    email,
    created_at,
    age,
    status,
    region,
    _load_timestamp
from {{ ref('raw_customers') }}
