-- Order summary by customer
-- Aggregates order data with quality filters applied

SELECT
    o.customer_id,
    c.name AS customer_name,
    c.region,
    COUNT(o.order_id) AS total_orders,
    SUM(o.amount) AS total_amount,
    AVG(o.amount) AS avg_order_value,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date
FROM {{ ref('stg_orders') }} o
INNER JOIN {{ ref('cleaned_customers') }} c
    ON o.customer_id = c.customer_id
WHERE
    -- Validity: only include positive amounts
    o.amount > 0
    -- Completeness: require amounts
    AND o.amount IS NOT NULL
GROUP BY
    o.customer_id,
    c.name,
    c.region

