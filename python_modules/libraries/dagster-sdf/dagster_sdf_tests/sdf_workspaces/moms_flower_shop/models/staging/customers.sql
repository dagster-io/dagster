SELECT 
    c.id AS customer_id,
    c.first_name,
    c.last_name,
    c.first_name || ' ' || c.last_name AS full_name,
    c.email,
    c.gender,
    
    -- Marketing info
    i.campaign_id,
    i.campaign_name,
    i.campaign_type,

    -- Address info
    c.address_id,
    a.full_address,
    a.state
FROM raw.raw_customers c 

    LEFT OUTER JOIN app_installs_v2 i
        ON (c.id = i.customer_id)

    LEFT OUTER JOIN raw.raw_addresses a
        ON (c.address_id = a.address_id)
