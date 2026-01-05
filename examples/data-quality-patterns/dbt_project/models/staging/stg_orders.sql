-- Staging model for order data
-- Selects from the raw.orders table populated by Dagster

SELECT
    order_id,
    customer_id,
    amount,
    order_date,
    status
FROM {{ source('raw', 'orders') }}

