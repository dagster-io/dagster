-- ============================================================
-- Setup SQL for Snowflake Dynamic Tables Example
-- Run this once in your Snowflake environment before using
-- the Dagster example. Replace <YOUR_WAREHOUSE> with your
-- Snowflake warehouse name.
-- ============================================================

USE DATABASE ECOMMERCE;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;

-- ============================================================
-- Source tables (normally loaded by your ETL pipeline)
-- ============================================================

CREATE TABLE IF NOT EXISTS RAW.RAW_ORDERS (
    order_id    VARCHAR(50)    NOT NULL,
    customer_id VARCHAR(50)    NOT NULL,
    order_date  DATE           NOT NULL,
    revenue     DECIMAL(12, 2) NOT NULL,
    status      VARCHAR(20)    DEFAULT 'completed',
    created_at  TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (order_id)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_CUSTOMERS (
    customer_id VARCHAR(50)  NOT NULL,
    email       VARCHAR(255),
    first_name  VARCHAR(100),
    last_name   VARCHAR(100),
    created_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (customer_id)
);

-- ============================================================
-- Dynamic Table 1: CUSTOMER_LIFETIME_VALUE
-- TARGET_LAG = '1 minute', REFRESH_MODE = INCREMENTAL
-- Snowflake automatically refreshes this every ~1 minute.
-- Dagster represents this as a virtual asset — it is never
-- executed by Dagster.
-- ============================================================

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.CUSTOMER_LIFETIME_VALUE
    TARGET_LAG    = '1 minute'
    WAREHOUSE     = <YOUR_WAREHOUSE>
    REFRESH_MODE  = INCREMENTAL
AS
SELECT
    c.customer_id,
    c.email,
    c.first_name,
    c.last_name,
    COUNT(o.order_id)   AS order_count,
    SUM(o.revenue)      AS lifetime_value,
    MIN(o.order_date)   AS first_order_date,
    MAX(o.order_date)   AS latest_order_date,
    CURRENT_TIMESTAMP() AS computed_at
FROM RAW.RAW_CUSTOMERS c
LEFT JOIN RAW.RAW_ORDERS o
    ON  c.customer_id = o.customer_id
    AND o.status = 'completed'
GROUP BY
    c.customer_id, c.email, c.first_name, c.last_name;

-- ============================================================
-- Dynamic Table 2: DAILY_REVENUE_ROLLUP
-- TARGET_LAG = '1 hour', REFRESH_MODE = FULL
-- Snowflake automatically refreshes this every ~1 hour.
-- Dagster represents this as a virtual asset — it is never
-- executed by Dagster.
-- ============================================================

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DAILY_REVENUE_ROLLUP
    TARGET_LAG    = '1 hour'
    WAREHOUSE     = <YOUR_WAREHOUSE>
    REFRESH_MODE  = FULL
AS
SELECT
    order_date,
    COUNT(DISTINCT order_id)    AS order_count,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(revenue)                AS revenue,
    AVG(revenue)                AS avg_order_value
FROM RAW.RAW_ORDERS
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date;

-- ============================================================
-- Verify the tables were created
-- ============================================================

SHOW DYNAMIC TABLES IN SCHEMA ANALYTICS;

SELECT name, refresh_mode, target_lag, scheduling_state
FROM information_schema.dynamic_tables
WHERE schema_name = 'ANALYTICS';
