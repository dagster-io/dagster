PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

CREATE VIEW report_active_customers_by_product_daily AS
WITH static_data(dim_day_ts, customer_id, customer_name, product_id, product_name) AS ( VALUES
    ('2021-12-01', 'cust-001', 'Customer 001', 'prod-001', 'Product 001'),
    ('2021-12-01', 'cust-002', 'Customer 002', 'prod-001', 'Product 001')
)

SELECT
       dim_day_ts
     , customer_id
     , customer_name
     , product_id
     , product_name
FROM static_data;

COMMIT;
