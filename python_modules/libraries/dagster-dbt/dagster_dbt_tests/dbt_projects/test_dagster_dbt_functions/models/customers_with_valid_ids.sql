{#- a model that depends on a dbt function (UDF), which creates function -> model lineage -#}

select
    customer_id,
    {{ function('is_positive_int') }}(cast(customer_id as varchar)) as has_valid_id

from {{ ref('stg_customers') }}
