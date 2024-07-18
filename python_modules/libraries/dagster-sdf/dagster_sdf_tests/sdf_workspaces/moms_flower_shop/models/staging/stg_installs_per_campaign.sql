SELECT 
    campaign_id,
    COUNT(event_id) AS total_num_installs
FROM app_installs_v2
GROUP BY 1
