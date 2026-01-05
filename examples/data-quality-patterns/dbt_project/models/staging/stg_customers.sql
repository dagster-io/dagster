-- Staging model for customer data
-- Selects from the raw.customers table populated by Dagster

SELECT
    customer_id,
    email,
    name,
    region,
    created_at,
    age,
    status
FROM {{ source('raw', 'customers') }}

