-- start_stg_feed_snapshots
WITH raw AS (
    SELECT * FROM {{ source('r2_bucket', 'actor_feed_snapshot') }}
)

SELECT * FROM raw
-- end_stg_feed_snapshots