WITH raw AS (
    SELECT * FROM {{ source('r2_bucket', 'actor_feed_snapshot') }}
)

SELECT * FROM raw
