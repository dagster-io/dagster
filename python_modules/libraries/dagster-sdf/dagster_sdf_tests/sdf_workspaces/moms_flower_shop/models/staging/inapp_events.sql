SELECT 
    event_id,
    customer_id,
    FROM_UNIXTIME(event_time/1000) AS event_time,  
    event_name,
    event_value,
    additional_details,
    platform,
    campaign_id
FROM raw.raw_inapp_events