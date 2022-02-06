PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE fact_usage_daily
(
    dim_day_ts TIMESTAMP not null,
    dim_deployment_id VARCHAR not null,
    usage_quantity NUMERIC(10,2) not null,
    usage_unit VARCHAR not null
);
INSERT INTO fact_usage_daily VALUES('2021-12-05','d:1',10,'vCPUs');
INSERT INTO fact_usage_daily VALUES('2021-12-20','d:1',100,'vCPUs');
INSERT INTO fact_usage_daily VALUES('2021-12-20','d:2',100,'vCPUs');
CREATE TABLE dim_deployment_daily
(
    dim_day_ts DATE not null,
    dim_deployment_id VARCHAR not null,
    dim_product_id VARCHAR not null,
    dim_customer_id VARCHAR not null
);
INSERT INTO dim_deployment_daily VALUES('2021-12-05','d:1','p:1','c:1');
INSERT INTO dim_deployment_daily VALUES('2021-12-20','d:1','p:1','c:1');
INSERT INTO dim_deployment_daily VALUES('2021-12-20','d:2','p:1','c:1');
CREATE TABLE dim_customer_daily
(
    dim_day_ts date not null,
    dim_customer_id VARCHAR not null,
    customer_id VARCHAR not null,
    customer_name VARCHAR not null
);
INSERT INTO dim_customer_daily VALUES('2021-12-05','c:1','CUST-001','Customer One');
INSERT INTO dim_customer_daily VALUES('2021-12-20','c:1','CUST-001','Customer One');
CREATE TABLE dim_product_daily
(
    dim_day_ts DATE not null,
    dim_product_id VARCHAR not null,
    product_id VARCHAR not null,
    product_name VARCHAR not null
);
INSERT INTO dim_product_daily VALUES('2021-12-05','p:1','CLOUD1','Cloud Service');
INSERT INTO dim_product_daily VALUES('2021-12-20','p:1','CLOUD1','Cloud Service');


CREATE VIEW dim_day AS
    -- with thanks to https://gist.github.com/exocomet/fb4a588c7eb081f62ce3c8acb268293b
    WITH RECURSIVE dates(dim_day_ts) AS (
        VALUES ('2000-01-01')
        UNION ALL
        SELECT date(dim_day_ts, '+1 day')
        FROM dates
        WHERE dim_day_ts < '2039-01-01'
    )
    SELECT
           dim_day_ts,
       (CAST(strftime('%w', dim_day_ts) AS INT) + 6) % 7 AS dayofweek,
       CASE
               (CAST(strftime('%w', dim_day_ts) AS INT) + 6) % 7
           WHEN 0 THEN 'Monday'
           WHEN 1 THEN 'Tuesday'
           WHEN 2 THEN 'Wednesday'
           WHEN 3 THEN 'Thursday'
           WHEN 4 THEN 'Friday'
           WHEN 5 THEN 'Saturday'
           ELSE 'Sunday'
           END                                  AS weekday,
       CASE
           WHEN CAST(strftime('%m', dim_day_ts) AS INT) BETWEEN 1 AND 3 THEN 1
           WHEN CAST(strftime('%m', dim_day_ts) AS INT) BETWEEN 4 AND 6 THEN 2
           WHEN CAST(strftime('%m', dim_day_ts) AS INT) BETWEEN 7 AND 9 THEN 3
           ELSE 4
           END                                  AS quarter,
       CAST(strftime('%Y', dim_day_ts) AS INT)           AS year,
       CAST(strftime('%m', dim_day_ts) AS INT)           AS month,
       CAST(strftime('%d', dim_day_ts) AS INT)           AS day
FROM dates;

CREATE VIEW report_active_customers_by_product_daily AS
    WITH
        every_deployment_every_day AS (
    --  Generate a dataset containing a row for every deployment & day combination, eg:
    --  +-----------------+----------+
    --  |dim_deployment_id|dim_day_ts|
    --  +-----------------+----------+
    --  |d:1              |2000-01-01|  <-- First day in dim_day
    --  |d:1              |2000-01-02|
    --  |d:1              |2000-01-03|
    --  ... snip ...
    --  |d:1              |2042-01-01|  <-- Last day in dim_day
    --  |d:2              |2000-01-01|  <-- Repeat for next dim_deployment_id
    --  |d:2              |2000-01-02|
    --  |d:2              |2000-01-03|
    --  ... snip ...
    --  |d:2              |2042-01-01|
    --  etc for every dim_deployment_id
            SELECT
                dim_deployment_id
                 ,   dim_day_ts
            FROM dim_day
            CROSS JOIN (SELECT DISTINCT dim_deployment_id FROM fact_usage_daily)
        ),
        fact_usage_without_gaps AS (
    -- Add in actual usage (with NULL for days where there wasn't any), eg:
    -- +-----------------+----------+--------------+----------+
    -- |dim_deployment_id|dim_day_ts|usage_quantity|usage_unit|
    -- +-----------------+----------+--------------+----------+
    -- |d:1              |2021-12-04|NULL          |NULL      |
    -- |d:1              |2021-12-05|10.00         |vCPUs     |
    -- |d:1              |2021-12-06|NULL          |NULL      |
    -- ... snip ...
    -- |d:1              |2021-12-24|NULL          |NULL      |
    -- |d:1              |2021-12-25|100.00        |vCPUs     |
    -- |d:1              |2021-12-26|NULL          |NULL      |
    -- ... snip ...
    -- |d:2              |2021-12-24|NULL          |NULL      |
    -- |d:2              |2021-12-25|10.00         |vCPUs     |
    -- ... etc
            SELECT
                d.dim_deployment_id
                 ,   d.dim_day_ts
                 ,   f.usage_quantity
                 ,   f.usage_unit
            FROM every_deployment_every_day AS d
                     LEFT JOIN fact_usage_daily AS f
                               ON d.dim_day_ts = f.dim_day_ts
                                   AND d.dim_deployment_id = f.dim_deployment_id
        )
       , fact_usage_rolling_30_days AS (
    -- Calculate the rolling sum of usage using a window function over the last 30 rows (ie, days)
    -- +-----------------+----------+--------------+----------+--------------------------------+
    -- |dim_deployment_id|dim_day_ts|usage_quantity|usage_unit|usage_quantity_over_last_30_days|
    -- +-----------------+----------+--------------+----------+--------------------------------+
    -- |d:1              |2021-12-04|NULL          |NULL      |NULL                            |
    -- |d:1              |2021-12-05|10.00         |vCPUs     |10                              |
    -- |d:1              |2021-12-06|NULL          |NULL      |10                              |
    -- ...snip...
    -- |d:1              |2021-12-24|NULL          |NULL      |10                              |
    -- |d:1              |2021-12-25|100.00        |vCPUs     |110                             |
    -- |d:1              |2021-12-26|NULL          |NULL      |110                             |
    -- |d:1              |2021-12-27|NULL          |NULL      |110                             |
    -- ... etc
        SELECT
            f.*
             ,   SUM(usage_quantity) OVER (
            PARTITION BY dim_deployment_id
            ORDER BY dim_day_ts
            ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
            ) AS usage_quantity_over_last_30_days
        FROM fact_usage_without_gaps AS f
    )
    -- Filter to only keep deployments with usage in the last 30 days
    -- ie, the rolling 30 day usage value > 0
       , deployments_with_usage_in_last_30_days AS (
        SELECT
            dim_day_ts
             ,   dim_deployment_id
        FROM fact_usage_rolling_30_days
        WHERE usage_quantity_over_last_30_days > 0
    )
    -- Enrich the deployments with customer & product dimension information for dim_day_ts
    -- When there isn't dimension information available for a dim_day_ts take the most recently
    -- available dimension information prior to dim_day_ts - ie:
    -- +----------+-----------------+-----------+-------------+----------+-------------+
    -- |dim_day_ts|dim_deployment_id|customer_id|customer_name|product_id|product_name |
    -- +----------+-----------------+-----------+-------------+----------+-------------+
    -- |2021-12-05|d:1              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- .. snip ...
    -- |2021-12-18|d:1              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- |2021-12-19|d:1              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- |2021-12-20|d:1              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- |2021-12-20|d:2              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- |2021-12-21|d:1              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- |2021-12-21|d:2              |CUST-001   |Customer One |CLOUD1    |Cloud Service|
    -- etc
       , enriched_deployments_with_usage_in_last_30_days AS (
        SELECT f.dim_day_ts
             , f.dim_deployment_id
             , (
            SELECT c.customer_id
            FROM dim_deployment_daily AS d
                     JOIN dim_customer_daily AS c
                          ON d.dim_customer_id = c.dim_customer_id
            WHERE d.dim_deployment_id = f.dim_deployment_id
              AND d.dim_day_ts <= f.dim_day_ts
              AND c.dim_day_ts <= f.dim_day_ts
            ORDER BY d.dim_day_ts DESC
            LIMIT 1
        ) AS customer_id
             , (
            SELECT c.customer_name
            FROM dim_deployment_daily AS d
                     JOIN dim_customer_daily AS c
                          ON d.dim_customer_id = c.dim_customer_id
            WHERE d.dim_deployment_id = f.dim_deployment_id
              AND d.dim_day_ts <= f.dim_day_ts
              AND c.dim_day_ts <= f.dim_day_ts
            ORDER BY d.dim_day_ts DESC
            LIMIT 1
        ) AS customer_name
             , (
            SELECT p.product_id
            FROM dim_deployment_daily AS d
                     JOIN dim_product_daily AS p
                          ON d.dim_product_id = p.dim_product_id
            WHERE d.dim_deployment_id = f.dim_deployment_id
              AND d.dim_day_ts <= f.dim_day_ts
              AND p.dim_day_ts <= f.dim_day_ts
            ORDER BY d.dim_day_ts DESC
            LIMIT 1
        ) AS product_id
             , (
            SELECT p.product_name
            FROM dim_deployment_daily AS d
                     JOIN dim_product_daily AS p
                          ON d.dim_product_id = p.dim_product_id
            WHERE d.dim_deployment_id = f.dim_deployment_id
              AND d.dim_day_ts <= f.dim_day_ts
              AND p.dim_day_ts <= f.dim_day_ts
            ORDER BY d.dim_day_ts DESC
            LIMIT 1
        ) AS product_name
        FROM deployments_with_usage_in_last_30_days AS f
    )
    -- Finally, find the active customers / product / day by
    -- selecting the distinct combinations
    SELECT DISTINCT
        dim_day_ts
                  ,   customer_id
                  ,   customer_name
                  ,   product_id
                  ,   product_name
    FROM enriched_deployments_with_usage_in_last_30_days
;

COMMIT;
