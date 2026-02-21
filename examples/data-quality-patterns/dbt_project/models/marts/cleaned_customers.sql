-- Cleaned customer data mart
-- Filters out invalid records based on quality checks

SELECT
    customer_id,
    email,
    name,
    region,
    created_at,
    age,
    status
FROM {{ ref('stg_customers') }}
WHERE
    -- Completeness: require email
    email IS NOT NULL
    -- Validity: require proper region codes
    AND region IN ('US', 'EU', 'APAC', 'LATAM')
    -- Accuracy: require valid age range
    AND age BETWEEN 0 AND 120

