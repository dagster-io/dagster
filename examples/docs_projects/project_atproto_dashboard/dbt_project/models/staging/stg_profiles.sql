WITH raw AS (
    SELECT * FROM {{ source('r2_bucket', 'starter_pack_snapshot') }}
)

SELECT * FROM raw
