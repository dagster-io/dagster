

create or replace view moms_workshed.staging.inapp_events as (SELECT 
    event_id,
    customer_id,
    FROM_UNIXTIME(event_time/1000) AS event_time,  
    event_name,
    event_value,
    additional_details,
    platform,
    campaign_id
FROM moms_workshed.raw.raw_inapp_events);

