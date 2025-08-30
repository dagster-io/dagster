with
    trips as (
        select *
        from {{ ref('stg_trips') }}
    ),
    zones as (
        select *
        from {{ ref('stg_zones') }}
    ),
    trips_by_zone as (
        select
            pickup_zones.zone_name as zone,
            dropoff_zones.borough as destination_borough,
            pickup_zones.is_airport as from_airport,
            count(*) as trips,
            sum(trips.trip_distance) as total_distance,
            sum(trips.duration) as total_duration,
            sum(trips.total_amount) as fare,
            sum(case when duration > 30 then 1 else 0 end) as trips_over_30_min
        from trips
        left join zones as pickup_zones on trips.pickup_zone_id = pickup_zones.zone_id
        left join zones as dropoff_zones on trips.dropoff_zone_id = dropoff_zones.zone_id
        group by all
    )
select *
from trips_by_zone
