{{ config(materialized='table', schema='silver') }}

-- Silver layer: Cleaned and validated customer data
-- This model cleans, validates, and standardizes data from bronze layer

with bronze_data as (
    select * from {{ ref('bronze_customers') }}
),

cleaned as (
    select
        customer_id,
        lower(trim(email)) as email,
        try_to_timestamp(created_at) as created_at,
        case
            when age between 0 and 150 then age
            else null
        end as age,
        upper(trim(status)) as status,
        upper(trim(region)) as region,
        _load_timestamp
    from bronze_data
    where email is not null
        and email like '%@%.%'
        and customer_id is not null
),

deduplicated as (
    select *
    from cleaned
    qualify row_number() over (
        partition by customer_id
        order by _load_timestamp desc
    ) = 1
)

select * from deduplicated
