{{ config(materialized='table', schema='gold') }}

-- Gold layer: Curated customer summary for business consumption
-- This model aggregates and enriches data from silver layer

with silver_data as (
    select * from {{ ref('silver_customers') }}
),

customer_segments as (
    select
        region,
        status,
        case
            when age < 30 then 'young'
            when age < 50 then 'middle'
            else 'senior'
        end as age_group,
        count(*) as customer_count,
        avg(age) as avg_age,
        current_timestamp() as summary_timestamp
    from silver_data
    where age is not null
    group by region, status, age_group
)

select * from customer_segments
