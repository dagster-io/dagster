
-- metricflow_time_spine.sql
with

days as (

    --for BQ adapters use "DATE('01/01/2000','mm/dd/yyyy')"
    {{ dbt_date.get_base_dates(n_dateparts=365*10, datepart="day") }}

),

cast_to_date as (

    select
        cast(date_day as date) as date_day

    from days

)

select * from cast_to_date
