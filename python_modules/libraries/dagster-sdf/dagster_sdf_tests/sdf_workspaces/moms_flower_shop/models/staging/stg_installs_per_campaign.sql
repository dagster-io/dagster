SELECT 
    campaign_id,
    COUNT(event_id) AS total_num_installs
FROM app_installs
GROUP BY 1
