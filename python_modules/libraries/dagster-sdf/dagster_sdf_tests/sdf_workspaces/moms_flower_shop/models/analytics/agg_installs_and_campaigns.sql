SELECT 
    -- install events data
    DATE_FORMAT(install_time, '%Y-%m-%d') AS install_date,
    campaign_name,
    platform,
    COUNT(DISTINCT customer_id) AS distinct_installs
FROM staging.app_installs
GROUP BY 1,2,3