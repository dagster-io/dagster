

create or replace view moms_workshed.analytics.dim_marketing_campaigns as (SELECT 
    -- marketing campaigns dimensions
    m.campaign_id,
    m.campaign_name,
    -- metrics
    i.total_num_installs,
    total_campaign_spent / 
        NULLIF(i.total_num_installs, 0) AS avg_customer_acquisition_cost,
    campaign_duration / 
        NULLIF(i.total_num_installs, 0) AS install_duration_ratio
FROM moms_workshed.staging.marketing_campaigns m
    LEFT OUTER JOIN moms_workshed.staging.stg_installs_per_campaign i
    ON (m.campaign_id = i.campaign_id)
ORDER BY total_num_installs DESC NULLS LAST);

