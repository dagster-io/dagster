with raw as (
    select * from {{ source('r2_bucket', 'starter_pack_snapshot') }}
)

select * from raw
