

create or replace view moms_workshed.analytics.agg_installs_and_campaigns as (SELECT 
    -- install events data
    DATE_FORMAT(install_time, '%Y-%m-%d') AS install_date,
    campaign_name,
    platform,
    COUNT(DISTINCT customer_id) AS distinct_installs
FROM moms_workshed.staging.app_installs_v2
GROUP BY 1,2,3);

