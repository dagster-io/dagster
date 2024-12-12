with raw as (
    select * from {{source('r2_bucket', 'actor_feed_snapshot')}}
)
Select * from raw