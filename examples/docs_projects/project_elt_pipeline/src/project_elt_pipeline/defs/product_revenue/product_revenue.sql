CREATE OR REPLACE TABLE product_revenue AS
SELECT
    p.id          AS product_id,
    p.name,
    COUNT(o.id)   AS order_count,
    SUM(o.total)  AS total_revenue
FROM products p
LEFT JOIN orders o ON o.product_id = p.id
GROUP BY p.id, p.name
