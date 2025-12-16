{{ config(materialized='table', schema='bronze') }}

-- Bronze layer: Raw customer data
-- This model loads raw data from source systems
-- No transformations, just raw data preservation

select
    customer_id,
    email,
    created_at,
    age,
    status,
    region,
    _load_timestamp
from {{ source('raw', 'customers') }}
