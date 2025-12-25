{{ config(materialized='table', schema='bronze') }}

-- Bronze layer: Raw data ingestion
-- This model represents the first layer of the medallion architecture.
-- In production, this would typically ingest from external sources (APIs, files, etc.).
-- For this example, it reads from a seed file to demonstrate the pattern.

select
    customer_id,
    email,
    created_at,
    age,
    status,
    region,
    _load_timestamp
from {{ ref('raw_customers') }}
