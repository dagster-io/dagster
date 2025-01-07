

create or replace view moms_workshed.staging.app_installs as (SELECT 
    -- install events data
    COALESCE(m.event_id, i.event_id) AS event_id,
    i.customer_id,
    i.event_time AS install_time,
    i.platform,

    -- marketing campaigns data - if doesn't exist than organic
    COALESCE(m.campaign_id, -1) AS campaign_id, 
    COALESCE(m.campaign_name, 'organic') AS campaign_name,
    COALESCE(m.c_name, 'organic') AS campaign_type
FROM moms_workshed.staging.inapp_events i 
    LEFT OUTER JOIN moms_workshed.raw.raw_marketing_campaign_events m
        ON (i.event_id = m.event_id) 
WHERE event_name = 'install');

comment if exists on view moms_workshed.staging.app_installs IS 'This table is a staging table which adds campaign information to app install events
';
