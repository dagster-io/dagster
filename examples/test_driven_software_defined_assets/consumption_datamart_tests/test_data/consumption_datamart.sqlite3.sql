PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE fact_usage_daily
(
	dim_day_ts TIMESTAMP not null,
	dim_deployment_id VARCHAR not null,
	dim_product_id VARCHAR not null,
	usage_quantity NUMERIC(10,2) not null,
	usage_unit VARCHAR not null
);
CREATE TABLE dim_deployment_daily
(
	dim_day_ts DATE not null,
	dim_deployment_id VARCHAR not null,
	dim_customer_id VARCHAR not null
);
CREATE TABLE dim_customer_daily
(
	dim_day_ts date not null,
	dim_customer_id VARCHAR not null,
	customer_name VARCHAR not null
);
CREATE TABLE dim_product_daily
(
	dim_day_ts DATE not null,
	dim_product_id VARCHAR not null,
	product_name VARCHAR
);
COMMIT;
