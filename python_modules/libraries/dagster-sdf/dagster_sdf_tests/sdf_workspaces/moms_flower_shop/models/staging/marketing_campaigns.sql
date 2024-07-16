SELECT 
    campaign_id,
    campaign_name,
    SUBSTR(c_name, 1, LENGTH(c_name)-1) AS campaign_type,
    MIN(
        FROM_UNIXTIME(event_time/1000) -- convert unixtime from milliseconds to seconds
    ) AS start_time,
    MAX(
        FROM_UNIXTIME(event_time/1000) -- convert unixtime from milliseconds to seconds
    ) AS end_time,
    COUNT(event_time) AS campaign_duration,
    SUM(cost) AS total_campaign_spent,
    ARRAY_AGG(event_id) AS event_ids
FROM raw.raw_marketing_campaign_events
GROUP BY 
    campaign_id,
    campaign_name,
    campaign_type
