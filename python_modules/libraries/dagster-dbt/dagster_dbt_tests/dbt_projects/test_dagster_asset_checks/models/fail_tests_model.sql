with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ ref('raw_fail_tests_model') }}

),

renamed as (

    select
        id,
        first_name,
        last_name

    from source

)

select * from renamed
