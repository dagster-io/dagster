

create or replace view moms_workshed.staging.stg_installs_per_campaign as (SELECT 
    campaign_id,
    COUNT(event_id) AS total_num_installs
FROM moms_workshed.staging.app_installs_v2
GROUP BY 1);

