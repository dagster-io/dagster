with
    raw_trips as (
        select *
        from {{ source('raw_taxis', 'trips') }}
    )
select
    {{
        dbt_utils.generate_surrogate_key([
            'partition_date',
            'pickup_zone_id',
            'dropoff_zone_id',
            'pickup_datetime',
            'dropoff_datetime',
        ])
    }} as trip_id,
    date_diff('minutes', pickup_datetime, dropoff_datetime) as duration,
    case payment_type
        when 0 then 'Unknown'
        when 1 then 'Credit Card'
        when 2 then 'Cash'
        when 3 then 'No Charge'
        when 4 then 'Dispute'
        when 5 then 'Unknown'
        when 6 then 'Voided Trip'
    end as payment_type,
    case rate_code_id
        when 1 then 'Standard rate'
        when 2 then 'JFK'
        when 3 then 'Newark'
        when 4 then 'Nassau or Westchester'
        when 5 then 'Negotiated fare'
        when 6 then 'Group ride'
        when 99 then 'Unknown'
        else 'Unknown'
    end as rate_code,
    case vendor_id
        when '1' then 'Creative Mobile Technologies, LLC'
        when '2' then 'VeriFone Inc.'
        else 'Unknown'
    end as vendor_name,
    *
    exclude (
        payment_type,
        rate_code_id,
        vendor_id
    )
from raw_trips