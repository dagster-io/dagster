CREATE OR REPLACE TABLE customer_order_summary AS
SELECT
    u.id         AS user_id,
    u.name,
    u.email,
    COUNT(o.id)  AS order_count,
    SUM(o.total) AS lifetime_value
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.name, u.email
