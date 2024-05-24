with source as (

    {#-
    Normally we would select from the table here, but we are using sources to load
    our data in this project
    #}
    select * from {{ source('jaffle_shop', 'raw_customers') }}

),

renamed as (

    select
        id as customer_id,
        first_name,
        last_name

    from source

)

select * from renamed
