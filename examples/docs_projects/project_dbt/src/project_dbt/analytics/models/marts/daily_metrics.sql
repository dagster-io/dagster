{{
  config(
    materialized='incremental',
    unique_key='date_of_business'
  )
}}

with
    trips as (
        select *
        from {{ ref('stg_trips') }}
    ),
    daily_summary as (
        select
            date_trunc('day', pickup_datetime) as date_of_business,
            count(*) as trip_count,
            sum(duration) as total_duration,
            sum(duration) / count(*) as average_duration,
            sum(total_amount) as total_amount,
            sum(total_amount) / count(*) as average_amount,
            sum(case when duration > 30 then 1 else 0 end) / count(*) as pct_over_30_min
        from trips
        group by all
    )
select *
from daily_summary
{% if is_incremental() %}
    where date_of_business between '{{ var('min_date') }}' and '{{ var('max_date') }}'
{% endif %}