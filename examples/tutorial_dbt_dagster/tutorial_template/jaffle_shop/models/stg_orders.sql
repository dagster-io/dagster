-- Refer to Using dbt with Dagster, part one for info about this file:
-- https://docs.dagster.io/integrations/dbt/using-dbt-with-dagster/part-one

with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ ref('raw_orders') }}

),

renamed as (

    select
        id as order_id,
        user_id as customer_id,
        order_date,
        status

    from source

)

select * from renamed