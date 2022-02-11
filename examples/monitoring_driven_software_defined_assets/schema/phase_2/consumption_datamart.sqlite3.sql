PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

CREATE TABLE report_active_customers_by_product_daily
(
    dim_day_ts DATE not null,
    customer_id VARCHAR not null,
    customer_name VARCHAR not null,
    product_id VARCHAR not null,
    product_name VARCHAR not null,
    meta__warnings VARCHAR,
    meta__partition INTEGER,
    meta__partition_type VARCHAR
);

COMMIT;
